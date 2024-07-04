from __future__ import division

import math
import struct
import sys
import time
from queue import Queue
from typing import Any, Generator, Iterable, Union

import numpy as np
import pyaudio
from google.cloud import speech
from six.moves import queue  # type: ignore

from .err_handler import ignoreStderr

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms


class MicrophoneStream(object):
    """
    マイクから音声をストリーミングするためのクラス。

    """

    def __init__(
        self,
        rate: float,
        chunk: float,
        _timeout_thresh: float = 0.5,
        _start_timeout_thresh: float = 4.0,
        _db_thresh: float = 55.0,
    ) -> None:
        """クラスの初期化メソッド。

        Args:
            rate (float): サンプリングレート。
            chunk (float): チャンクサイズ。
            _timeout_thresh (float): 音声が停止したと判断するタイムアウト閾値（秒）。デフォルトは0.5秒。
            _start_timeout_thresh (float): マイクの入力が開始しないまま終了するまでのタイムアウト閾値（秒）。デフォルトは4.0秒。
            _db_thresh (float): 音声が開始されたと判断する音量閾値（デシベル）。デフォルトは55.0デシベル。

        """
        self._rate = rate
        self._chunk = chunk
        self._buff: Queue[Union[None, bytes]] = queue.Queue()
        self.closed = True
        self.is_start = False
        self.is_start_callback = False
        self.is_finish = False
        self.timeout_thresh = _timeout_thresh
        # マイクの入力が開始しないまま終了するまでのthreshold時間[s]
        self.start_timeout_thresh = _start_timeout_thresh
        self.db_thresh = _db_thresh
        language_code = "ja-JP"  # a BCP-47 language tag
        self.client = speech.SpeechClient()
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=RATE,
            language_code=language_code,
        )
        self.streaming_config = speech.StreamingRecognitionConfig(
            config=config, interim_results=True
        )

    def __enter__(self) -> Any:
        """PyAudioストリームを開く。"""
        with ignoreStderr():
            self._audio_interface = pyaudio.PyAudio()
            self._audio_stream = self._audio_interface.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self._rate,
                input=True,
                frames_per_buffer=self._chunk,
                stream_callback=self._fill_buffer,
            )
            self.closed = False
            return self

    def __exit__(
        self,
        rate: float,
        chunk: float,
        _timeout_thresh: float = 0.5,
        _start_timeout_thresh: float = 4.0,
        _db_thresh: float = 55.0,
    ) -> None:
        """PyAudioストリームを閉じます。

        Args:
            rate (float): サンプリングレート。
            chunk (float): チャンクサイズ。
            _timeout_thresh (float, optional): 音声が停止したと判断するタイムアウト閾値（秒）。デフォルトは0.5秒。
            _start_timeout_thresh (float): マイクの入力が開始しないまま終了するまでのタイムアウト閾値（秒）。デフォルトは4.0秒。
            _db_thresh (float, optional): 音声が開始されたと判断する音量閾値（デシベル）。デフォルトは55.0デシベル。

        """
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()
        self.is_start_callback = False

    def start_callback(self) -> None:
        """開始コールバックを呼び出す。"""
        self.is_start_callback = True

    def _fill_buffer(
        self, in_data: bytes, frame_count: int, time_info: Any, status_flags: Any
    ) -> Union[None, Any]:
        """マイクからの入力データをバッファーに書き込む。

        Args:
            in_data (bytes): 入力データ
            frame_count (int): フレーム数
            time_info (Any): 時間
            status_flags (Any): ステータスフラグ

        Returns:
            Union[None, Any]: Noneまたは続行のためのフラグ

        """
        if self.is_start_callback:
            in_data2 = struct.unpack(f"{len(in_data) / 2:.0f}h", in_data)
            rms = math.sqrt(np.square(in_data2).mean())
            power = 20 * math.log10(rms) if rms > 0.0 else -math.inf  # RMS to db
            if power > self.db_thresh:
                if not self.is_start:
                    self.is_start = True
                self.start_time = time.time()
            if self.is_start:
                self._buff.put(in_data)
                if time.time() - self.start_time >= self.timeout_thresh:
                    self.closed = True
            else:
                if time.time() - self.start_time >= self.start_timeout_thresh:
                    self.closed = True
        return None, pyaudio.paContinue

    def generator(self) -> Union[None, Generator[Any, None, None]]:
        """bufferから音声データを生成するジェネレーター

        Yields:
            Union[None, Any]: 音声データ
        """
        while not self.closed:
            try:
                chunk = self._buff.get(block=False, timeout=0.01)
                if chunk is None:
                    return
                data = [chunk]
                while True:
                    try:
                        chunk = self._buff.get(block=False)
                        if chunk is None:
                            return
                        data.append(chunk)
                    except queue.Empty:
                        break
                yield b"".join(data)
            except queue.Empty:
                time.sleep(0.01)
                continue

    def transcribe(self) -> Iterable[speech.StreamingRecognizeResponse]:
        """ストリームからの音声をGoogle Cloud Speech-to-Text APIでテキストに変換する。

        Returns:
            Iterable[speech.StreamingRecognizeResponse]: ストリーミング認識の応答
        """
        audio_generator = self.generator()
        self.start_time = time.time()
        self.start_callback()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )
        responses = self.client.streaming_recognize(self.streaming_config, requests)
        return responses


def get_db_thresh() -> float:
    """マイクからの周囲音量を測定。

    Returns:
        float: 測定された音量[db]
    """
    with ignoreStderr():
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )
        frames = []
        print("Measuring Ambient Sound Levels…")
        for _ in range(int(RATE / CHUNK * 2)):
            data = stream.read(CHUNK)
            frames.append(data)
        audio_data = np.frombuffer(b"".join(frames), dtype=np.int16)
        rms2 = np.square(audio_data).mean()
        if rms2 > 0.0:
            rms = math.sqrt(np.square(audio_data).mean())
            power = 20 * math.log10(rms) if rms > 0.0 else -math.inf  # RMS to db
        else:
            power = 20
        print(f"Sound Levels: {power:.3f}db")
        stream.stop_stream()
        stream.close()
        p.terminate()
    return power


def listen_print_loop(responses: Any) -> str:
    """Google Cloud Speech-to-Text APIの応答からテキストを取得し、リアルタイムで出力。

    Args:
        responses (Any): ストリーミング認識の応答

    Returns:
        str: 認識されたテキスト

    """
    num_chars_printed = 0
    transcript = ""
    overwrite_chars = ""
    for response in responses:
        if response.error.code:
            break
        if not response.results:
            continue
        result = response.results[0]
        if not result.alternatives:
            continue
        transcript = result.alternatives[0].transcript
        overwrite_chars = " " * (num_chars_printed - len(transcript))
        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + "\r")
            sys.stdout.flush()
            num_chars_printed = len(transcript)
        else:
            print(transcript + overwrite_chars)
            break
    return transcript + overwrite_chars
