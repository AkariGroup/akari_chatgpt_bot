from __future__ import division

import math
import struct
import sys
import time
import threading
from queue import Queue
from typing import Any, Generator, Iterable, Union

import numpy as np
import pyaudio
from google.cloud import speech
from six.moves import queue  # type: ignore

from .err_handler import ignoreStderr
from .google_webrtc import GoogleWebrtc


class MicrophoneStream(object):
    """
    マイクから音声をストリーミングするためのクラス。

    """

    def __init__(
        self,
        rate: float = 16000,
        chunk: float = 1600,
    ) -> None:
        """クラスの初期化メソッド。

        Args:
            rate (float): サンプリングレート。
            chunk (float): チャンクサイズ。

        """
        self._rate = rate
        self._chunk = chunk
        self._buff: Queue[Union[None, bytes]] = queue.Queue()
        self.closed = True
        self.is_start = False
        self.is_start_callback = False
        self.is_finish = False
        self.vad_state = False
        language_code = "ja-JP"  # a BCP-47 language tag
        self.client = speech.SpeechClient()
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self._rate,
            language_code=language_code,
        )
        self.streaming_config = speech.StreamingRecognitionConfig(
            config=config, interim_results=True
        )
        self.google_webrtc = GoogleWebrtc()
        self.vad_thread = threading.Thread(
            target=self.google_webrtc.vad_loop, args=(self.vad_callback,)
        )
        self.vad_thread.start()

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

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """PyAudioストリームを閉じる。

        Args:
            rate (float): サンプリングレート。
            chunk (float): チャンクサイズ。

        """
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()
        self.is_start_callback = False
        self.vad_thread.join()

    def vad_callback(self, flag) -> None:
        """Vadの状態変更コールバックを呼び出す。"""
        self.vad_state = flag

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
            self._buff.put(in_data)
            if self.vad_state:
                self.is_start = True
                self.start_time = time.time()
            if self.is_start and not self.vad_state:
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
        self.start_callback()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )
        responses = self.client.streaming_recognize(self.streaming_config, requests)
        return responses


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
