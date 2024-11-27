from __future__ import division

import math
import os
import struct
import sys
import time
from typing import Any, Optional, Union

import grpc
import numpy as np
import pyaudio

from .google_speech import MicrophoneStream

sys.path.append(os.path.join(os.path.dirname(__file__), "grpc"))
import gpt_server_pb2
import gpt_server_pb2_grpc
import motion_server_pb2
import motion_server_pb2_grpc
import voice_server_pb2
import voice_server_pb2_grpc


class MicrophoneStreamGrpc(MicrophoneStream):
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
        gpt_host: str = "127.0.0.1",
        gpt_port: str = "10001",
        voice_host: str = "127.0.0.1",
        voice_port: str = "10002",
        motion_server_host: Optional[str] = "127.0.0.1",
        motion_server_port: Optional[str] = "50055",
    ) -> None:
        """クラスの初期化メソッド。

        Args:
            rate (float): サンプリングレート。
            chunk (float): チャンクサイズ。
            _timeout_thresh (float): 音声が停止したと判断するタイムアウト閾値（秒）。デフォルトは0.5秒。
            _db_thresh (float): 音声が開始されたと判断する音量閾値（デシベル）。デフォルトは55.0デシベル。
            gpt_host (str, optional): GPTサーバーのホスト名。デフォルトは"127.0.0.1"。
            gpt_port (str, optional): GPTサーバーのポート番号。デフォルトは"10001"。
            voice_host (str, optional): VoiceVoxサーバーのホスト名。デフォルトは"127.0.0.1"。
            voice_port (str, optional): VoiceVoxサーバーのポート番号。デフォルトは"10002"。
            motion_server_host (str, optional): モーションサーバーのIPアドレス。デフォルトは"127.0.0.1"。
            motion_server_port (str, optional): モーションサーバーのポート番号。デフォルトは"50055"。
        """
        super().__init__(
            rate=rate,
            chunk=chunk,
            _timeout_thresh=_timeout_thresh,
            _start_timeout_thresh=_start_timeout_thresh,
            _db_thresh=_db_thresh,
        )
        gpt_channel = grpc.insecure_channel(gpt_host + ":" + gpt_port)
        self.gpt_stub = gpt_server_pb2_grpc.GptServerServiceStub(gpt_channel)
        voice_channel = grpc.insecure_channel(voice_host + ":" + voice_port)
        self.voice_stub = voice_server_pb2_grpc.VoiceServerServiceStub(voice_channel)
        self.motion_stub = None
        if motion_server_host is not None and motion_server_port is not None:
            motion_channel = grpc.insecure_channel(
                motion_server_host + ":" + motion_server_port
            )
            self.motion_stub = motion_server_pb2_grpc.MotionServerServiceStub(
                motion_channel
            )

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
                    if self.motion_stub is not None:
                        try:
                            self.motion_stub.SetMotion(
                                motion_server_pb2.SetMotionRequest(
                                    name="nod", priority=3, repeat=True
                                )
                            )
                        except BaseException:
                            pass
                self.start_time = time.time()
            if self.is_start:
                self._buff.put(in_data)
                if time.time() - self.start_time >= self.timeout_thresh:
                    self.closed = True
                    try:
                        self.voice_stub.SetVoicePlayFlg(
                            voice_server_pb2.SetVoicePlayFlgRequest(flg=True)
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


class GoogleSpeechGrpc(object):
    """
    Google Speech-to-Text APIのレスポンスを処理するクラス。

    """

    def __init__(
        self,
        gpt_host: str = "127.0.0.1",
        gpt_port: str = "10001",
        voice_host: str = "127.0.0.1",
        voice_port: str = "10002",
    ) -> None:
        """GoogleSpeechGrpcオブジェクトを初期化する。

        Args:
            gpt_host (str, optional): GPTサーバーのホスト名。デフォルトは"127.0.0.1"。
            gpt_port (str, optional): GPTサーバーのポート番号。デフォルトは"10001"。
            voice_host (str, optional): VoiceVoxサーバーのホスト名。デフォルトは"127.0.0.1"。
            voice_port (str, optional): VoiceVoxサーバーのポート番号。デフォルトは"10002"。
        """

        gpt_channel = grpc.insecure_channel(gpt_host + ":" + gpt_port)
        self.gpt_stub = gpt_server_pb2_grpc.GptServerServiceStub(gpt_channel)
        voice_channel = grpc.insecure_channel(voice_host + ":" + voice_port)
        self.voice_stub = voice_server_pb2_grpc.VoiceServerServiceStub(voice_channel)

    def listen_publisher_grpc(
        self, responses: Any, progress_report_len: int = 0
    ) -> str:
        """
        Google Cloud Speech-to-Text APIの応答からテキストを取得し、リアルタイムで出力。

        Args:
            responses (Any): ストリーミング認識の応答
            progress_report_len (int, optional): ここで指定した文字数以上になると、その時点で一度GPTに結果を送信する。0の場合は途中での送信は無効となる。デフォルトは0。

        Returns:
            str: 認識されたテキスト
        """
        is_progress_report = False
        num_chars_printed = 0
        transcript = ""
        overwrite_chars = ""
        try:
            self.voice_stub.SetVoicePlayFlg(
                voice_server_pb2.SetVoicePlayFlgRequest(flg=False)
            )
        except BaseException:
            print("SetVoicePlayFlg error")
            pass
        try:
            self.voice_stub.InterruptVoice(voice_server_pb2.InterruptVoiceRequest())
        except BaseException:
            print("InterruptVoice error")
            pass
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
                if not is_progress_report and num_chars_printed > progress_report_len:
                    if progress_report_len > 0:
                        try:
                            self.gpt_stub.SetGpt(
                                gpt_server_pb2.SetGptRequest(
                                    text=transcript + overwrite_chars, is_finish=False
                                )
                            )
                        except BaseException as e:
                            print("SetGpt error:", e)
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
                        except BaseException as e:
                            print("SetGpt error:", e)
                            pass
                break
        try:
            self.gpt_stub.SetGpt(
                gpt_server_pb2.SetGptRequest(
                    text=transcript + overwrite_chars, is_finish=True
                )
            )
        except BaseException as e:
            print("SetGpt error:", e)
            pass
        return transcript + overwrite_chars
