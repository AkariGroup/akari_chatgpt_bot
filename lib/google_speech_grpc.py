from __future__ import division

import math
import grpc
import os
import sys
import struct
import time
from queue import Queue
from typing import Any, Generator, Iterable, Union

import numpy as np
import pyaudio
from google.cloud import speech
from six.moves import queue  # type: ignore

from .err_handler import ignoreStderr

sys.path.append(os.path.join(os.path.dirname(__file__), "grpc"))
import gpt_server_pb2
import gpt_server_pb2_grpc
import voicevox_server_pb2
import voicevox_server_pb2_grpc

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms


class MicrophoneStreamGrpc(object):
    def __init__(
        self,
        rate: float,
        chunk: float,
        _timeout_thresh: float = 0.5,
        _db_thresh: float = 55.0,
        gpt_host: str = "127.0.0.1",
        gpt_port: str = "10001",
        voicevox_host: str = "127.0.0.1",
        voicevox_port: str = "10002",
    ) -> None:
        self._rate = rate
        self._chunk = chunk
        self._buff: Queue[Union[None, bytes]] = queue.Queue()
        self.closed = True
        self.is_start = False
        self.is_start_callback = False
        self.is_finish = False
        self.timeout_thresh = _timeout_thresh
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
        gpt_channel = grpc.insecure_channel(gpt_host + ":" + gpt_port)
        self.gpt_stub = gpt_server_pb2_grpc.GptServerServiceStub(gpt_channel)
        voicevox_channel = grpc.insecure_channel(voicevox_host + ":" + voicevox_port)
        self.voicevox_stub = voicevox_server_pb2_grpc.VoicevoxServerServiceStub(
            voicevox_channel
        )

    def __enter__(self) -> Any:
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
        _db_thresh: float = 55.0,
    ) -> None:
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()
        self.is_start_callback = False

    def start_callback(self) -> None:
        self.is_start_callback = True

    def _fill_buffer(
        self, in_data: bytes, frame_count: int, time_info: Any, status_flags: Any
    ) -> Union[None, Any]:
        if self.is_start_callback:
            self._buff.put(in_data)
            in_data2 = struct.unpack(f"{len(in_data) / 2:.0f}h", in_data)
            rms = math.sqrt(np.square(in_data2).mean())
            power = 20 * math.log10(rms) if rms > 0.0 else -math.inf  # RMS to db
            if power > self.db_thresh:
                self.is_start = True
            if power > self.db_thresh:
                self.start_time = time.time()
            if self.is_start and (time.time() - self.start_time >= self.timeout_thresh):
                self.closed = True
                try:
                    self.voicevox_stub.SetVoicePlayFlg(
                        voicevox_server_pb2.SetVoicePlayFlgRequest(flg=True)
                    )
                except BaseException:
                    print("SetVoicePlayFlg error")
                    pass
                try:
                    self.gpt_stub.SendMotion(gpt_server_pb2.SendMotionRequest())
                except BaseException:
                    print("Send motion error")
                    pass
                return None, pyaudio.paComplete
        return None, pyaudio.paContinue

    def generator(self) -> Union[None, Generator[Any, None, None]]:
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
        audio_generator = self.generator()
        self.start_callback()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )
        responses = self.client.streaming_recognize(self.streaming_config, requests)
        return responses


class GoogleSpeechGrpc(object):
    def __init__(
        self,
        gpt_host: str = "127.0.0.1",
        gpt_port: str = "10001",
        voicevox_host: str = "127.0.0.1",
        voicevox_port: str = "10001",
    ) -> None:
        gpt_channel = grpc.insecure_channel(gpt_host + ":" + gpt_port)
        self.gpt_stub = gpt_server_pb2_grpc.GptServerServiceStub(gpt_channel)
        voicevox_channel = grpc.insecure_channel(voicevox_host + ":" + voicevox_port)
        self.voicevox_stub = voicevox_server_pb2_grpc.VoicevoxServerServiceStub(
            voicevox_channel
        )

    def listen_publisher_grpc(
        self, responses: Any, progress_report_len: int = 0
    ) -> str:
        is_progress_report = False
        num_chars_printed = 0
        transcript = ""
        overwrite_chars = ""
        try:
            self.voicevox_stub.SetVoicePlayFlg(
                voicevox_server_pb2.SetVoicePlayFlgRequest(flg=False)
            )
        except BaseException:
            print("SetVoicePlayFlg error")
            pass
        try:
            self.voicevox_stub.InterruptVoicevox(
                voicevox_server_pb2.InterruptVoicevoxRequest()
            )
        except BaseException:
            print("InterruptVoicevox error")
            pass
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
                if not is_progress_report and num_chars_printed > progress_report_len:
                    if progress_report_len > 0:
                        try:
                            self.gpt_stub.SetGpt(
                                gpt_server_pb2.SetGptRequest(
                                    text=transcript + overwrite_chars, is_finish=False
                                )
                            )
                        except BaseException:
                            print("SetGpt error")
                            pass
                        is_progress_report = True
            else:
                if progress_report_len > 0:
                    if (
                        not is_progress_report
                        and num_chars_printed > progress_report_len
                    ):
                        try:
                            self.gpt_stub.SetGpt(
                                gpt_server_pb2.SetGptRequest(
                                    text=transcript + overwrite_chars, is_finish=False
                                )
                            )
                        except BaseException:
                            print("SetGpt error")
                            pass
                break
        try:
            self.gpt_stub.SetGpt(
                gpt_server_pb2.SetGptRequest(
                    text=transcript + overwrite_chars, is_finish=True
                )
            )
        except BaseException:
            print("SetGpt error")
            pass
        return transcript + overwrite_chars
