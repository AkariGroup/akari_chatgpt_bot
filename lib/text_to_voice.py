from abc import ABCMeta, abstractmethod
import io
import os
import sys
import time
import wave
from queue import Queue
from threading import Event, Thread
from typing import Any, Optional

import grpc
import numpy as np
import pyaudio
from lib.en_to_jp import EnToJp

from .err_handler import ignoreStderr

sys.path.append(os.path.join(os.path.dirname(__file__), "grpc"))
import motion_server_pb2
import motion_server_pb2_grpc


class TextToVoice(metaclass=ABCMeta):
    """
    音声合成を使用してテキストから音声を生成するクラス。
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: str = "52001",
        motion_host: Optional[str] = "127.0.0.1",
        motion_port: Optional[str] = "50055",
    ) -> None:
        """クラスの初期化メソッド。
        Args:
            host (str, optional): サーバーのホスト名。デフォルトは "127.0.0.1"。
            port (str, optional): サーバーのポート番号。デフォルトは "52001"。
            motion_host (str, optional): モーションサーバーのホスト名。デフォルトは"127.0.0.1"。
            motion_port (str, optional): モーションサーバーのポート番号。デフォルトは"50055"。

        """
        self.queue: Queue[str] = Queue()
        self.host = host
        self.port = port
        self.motion_stub = None
        if motion_host is not None or motion_port is not None:
            motion_channel = grpc.insecure_channel(motion_host + ":" + motion_port)
            self.motion_stub = motion_server_pb2_grpc.MotionServerServiceStub(
                motion_channel
            )
        self.finished = True  # 音声再生が完了したかどうかを示すフラグ
        self.sentence_end_flg = False  # 一文の終わりを示すフラグ
        self.sentence_end_timeout = 5.0  # 一文の終わりを判定するタイムアウト時間
        self.tilt_rate = 0.0  # 送信するtiltのrate(0.0~1.0)
        self.HEAD_RESET_INTERVAL = (
            0.3  # この時間更新がなければ、tiltの指令値を0にリセットする[sec]
        )
        self.TILT_GAIN = -0.8  # 音声出力の音量からtiltのrateに変換するゲイン
        self.TILT_RATE_DB_MAX = 40.0  # tilt_rate上限の音声出力値[dB]
        self.TILT_RATE_DB_MIN = 5.0  # tilt_rate下限の音声出力値[dB]
        self.TILT_ANGLE_MAX = 0.35  # Tiltの最大角度[rad]
        self.TILT_ANGLE_MIN = -0.1  # Tiltの最小角度[rad]
        self.HEAD_MOTION_INTERVAL = 0.15  # ヘッドモーションの更新周期[sec]
        self.event = Event()
        self.head_motion_thread = Thread(target=self.head_motion_control, daemon=True)
        if self.motion_stub is not None:
            self.head_motion_thread.start()
        self.text_to_voice_event = Event()
        self.voice_thread = Thread(target=self.text_to_voice_thread)
        self.voice_thread.start()
        self.en_to_jp = EnToJp()

    def __exit__(self) -> None:
        """音声合成スレッドを終了する。"""
        self.voice_thread.join()

    def sentence_end(self) -> None:
        """音声合成の一文の終わりを示すフラグを立てる。"""
        self.sentence_end_flg = True

    def enable_voice_play(self) -> None:
        """音声再生を開始する。"""
        self.text_to_voice_event.set()

    def disable_voice_play(self) -> None:
        """音声再生を停止する。"""
        self.text_to_voice_event.clear()

    def text_to_voice_thread(self) -> None:
        """
        音声合成スレッドの実行関数。
        キューからテキストを取り出し、text_to_voice関数を呼び出す。

        """
        last_queue_time = time.time()
        queue_start = False
        while True:
            self.text_to_voice_event.wait()
            if self.queue.qsize() > 0:
                queue_start = True
                last_queue_time = time.time()
                text = self.queue.get()
                # textに含まれる英語を極力かな変換する
                text = self.en_to_jp.text_to_kana(text, True, True, True)
                self.text_to_voice(text)
            else:
                # queueが空の状態でsentence_endが送られる、もしくはsentence_end_timeout秒経過した場合finishedにする。
                if self.sentence_end_flg or (
                    queue_start
                    and time.time() - last_queue_time > self.sentence_end_timeout
                ):
                    self.finished = True
                    queue_start = False
                    if self.motion_stub is not None:
                        print("Stop head control")
                        self.event.clear()
                        # 初期位置にヘッドを戻す
                        try:
                            self.motion_stub.SetPos(
                                motion_server_pb2.SetPosRequest(
                                    tilt=self.TILT_ANGLE_MAX, priority=3
                                )
                            )
                        except BaseException as e:
                            print(f"Failed to send SetPos command: {e}")
                            pass
                    self.sentence_end_flg = False
                    self.text_to_voice_event.clear()

    def put_text(
        self, text: str, play_now: bool = True, blocking: bool = False
    ) -> None:
        """
        音声合成のためのテキストをキューに追加する。

        Args:
            text (str): 音声合成対象のテキスト。
            play_now (bool, optional): すぐに音声再生を開始するかどうか。デフォルトはTrue。
            blocking (bool, optional): 音声合成が完了するまでブロックするかどうか。デフォルトはFalse。

        """
        if play_now:
            self.text_to_voice_event.set()
        self.queue.put(text)
        self.finished = False
        if blocking:
            self.wait_finish()

    def wait_finish(self) -> None:
        """
        音声合成が完了するまで待機するループ関数。

        """
        while not self.finished:
            time.sleep(0.01)

    @abstractmethod
    def set_param(
        self,
        speaker: Optional[int] = None,
        speed_scale: Optional[float] = None,
    ) -> None:
        """
        音声合成のパラメータを設定する。

        Args:
            speaker (Optional[int], optional): VoiceVoxの話者番号。デフォルトはNone。
            speed_scale (Optional[float], optional): 音声の再生速度スケール。デフォルトはNone。

        """
        ...

    def play_wav(self, wav_file: bytes) -> None:
        """合成された音声データを再生する。

        Args:
            wav_file (bytes): 合成された音声データ。

        """
        wr: wave.Wave_read = wave.open(io.BytesIO(wav_file))
        with ignoreStderr():
            p = pyaudio.PyAudio()
            stream = p.open(
                format=p.get_format_from_width(wr.getsampwidth()),
                channels=wr.getnchannels(),
                rate=wr.getframerate(),
                output=True,
            )
            chunk = 1024
            data = wr.readframes(chunk)
            while data:
                audio_data = np.frombuffer(data, dtype=np.int16)
                rms = np.sqrt(np.mean(audio_data**2))
                db = 20 * np.log10(rms) if rms > 0.0 else 0.0
                self.tilt_rate = self.db_to_head_rate(db)
                stream.write(data)
                data = wr.readframes(chunk)
            time.sleep(0.2)
            stream.close()
        p.terminate()

    @abstractmethod
    def text_to_voice(self, text: str) -> None:
        """
        テキストから音声を合成して再生する。

        Args:
            text (str): 音声合成対象のテキスト。

        """
        ...

    def is_playing(self) -> bool:
        """
        音声再生が実行中かどうかを返す。
        queueの中身が0かつ再生中の音声がなければFalseを返す。

        Returns:
            bool: 音声再生中の場合はTrue。

        """
        return self.finished

    def db_to_head_rate(self, db: float) -> float:
        """
        音声の音量[dB]からヘッドの動き具合を算出する。
        Args:
            db (float): 音声の音量[dB]。
        Returns:
            float: ヘッドの動き具合。
        """
        if db > self.TILT_RATE_DB_MAX:
            return 1.0
        elif db < self.TILT_RATE_DB_MIN:
            return 0.0
        return (db - self.TILT_RATE_DB_MIN) / (
            self.TILT_RATE_DB_MAX - self.TILT_RATE_DB_MIN
        )

    def head_motion_control(self) -> None:
        """
        音声出力に合わせてヘッドを動かす。
        """
        last_update_time = time.time()
        prev_tilt_rate = 0.0
        while True:
            self.event.wait()
            loop_start_time = time.time()
            if self.tilt_rate != prev_tilt_rate:
                val = (
                    -1 * self.tilt_rate * (self.TILT_ANGLE_MAX - self.TILT_ANGLE_MIN)
                    + self.TILT_ANGLE_MAX
                )
                if self.motion_stub is not None:
                    try:
                        self.motion_stub.ClearMotion(
                            motion_server_pb2.ClearMotionRequest(priority=3)
                        )
                    except BaseException as e:
                        print(f"Failed to ClearMotion command: {e}")
                        pass
                    try:
                        self.motion_stub.SetPos(
                            motion_server_pb2.SetPosRequest(tilt=val, priority=3)
                        )
                    except BaseException as e:
                        print(f"Failed to send SetPos command: {e}")
                        pass
                last_update_time = time.time()
                prev_tilt_rate = self.tilt_rate
            if time.time() - last_update_time > self.HEAD_RESET_INTERVAL:
                self.tilt_rate = 0.0
            wait_time = self.HEAD_MOTION_INTERVAL - (time.time() - loop_start_time)
            if wait_time > 0:
                time.sleep(wait_time)

    def start_head_control(self) -> None:
        """
        ヘッドモーションを開始する。
        """
        if self.motion_stub is not None:
            self.event.set()
