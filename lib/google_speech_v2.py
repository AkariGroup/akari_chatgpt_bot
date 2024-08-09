from __future__ import division

import math
import sys
import time
from queue import Queue
from typing import Iterable, Optional, Union

import numpy as np
import pyaudio

# from google.cloud import speech
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech as cloud_speech_types
from six.moves import queue  # type: ignore

from .conf import GOOGLE_SPEECH_PROJECT_ID
from .err_handler import ignoreStderr
from .google_speech import MicrophoneStream

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms


class MicrophoneStreamV2(MicrophoneStream):
    """
    マイクから音声をストリーミングするためのクラス。google STT v2用。

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
        language_codes = ["ja-JP"]  # a BCP-47 language tag
        self.client = SpeechClient()
        recognition_config = cloud_speech_types.RecognitionConfig(
            explicit_decoding_config=cloud_speech_types.ExplicitDecodingConfig(
                sample_rate_hertz=RATE,
                encoding=cloud_speech_types.ExplicitDecodingConfig.AudioEncoding.LINEAR16,
                audio_channel_count=1,
            ),
            language_codes=language_codes,
            model="long",
        )
        streaming_config = cloud_speech_types.StreamingRecognitionConfig(
            config=recognition_config,
            streaming_features=cloud_speech_types.StreamingRecognitionFeatures(
                interim_results=True
            ),
        )
        if GOOGLE_SPEECH_PROJECT_ID == "":
            raise ValueError("GOOGLE_SPEECH_PROJECT_ID is not set.")
        self.config_request = cloud_speech_types.StreamingRecognizeRequest(
            recognizer=f"projects/{GOOGLE_SPEECH_PROJECT_ID}/locations/global/recognizers/_",
            streaming_config=streaming_config,
        )

    def requests(
        self, config: cloud_speech_types.RecognitionConfig, audio: list
    ) -> list:
        yield config
        for chunk in audio:
            yield cloud_speech_types.StreamingRecognizeRequest(audio=chunk)

    def transcribe(
        self,
    ) -> Optional[Iterable[cloud_speech_types.StreamingRecognizeResponse]]:
        """ストリームからの音声をGoogle Cloud Speech-to-Text APIでテキストに変換する。

        Returns:
            Optional[Iterable[speech.StreamingRecognizeResponse]]: ストリーミング認識の応答
        """
        audio_generator = self.generator()
        self.start_time = time.time()
        self.start_callback()
        responses = None
        try:
            responses = self.client.streaming_recognize(
                requests=self.requests(self.config_request, audio_generator)
            )
        except BaseException:
            pass
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


def listen_print_loop(responses: object) -> str:
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
        # if response.error.code:
        #    break
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
