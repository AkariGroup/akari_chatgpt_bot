import io
import json
import os
import sys
import time
import wave
from queue import Queue
from threading import Event, Thread
from typing import Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import grpc
import numpy as np
import pyaudio
from lib.en_to_jp import EnToJp

from .err_handler import ignoreStderr

sys.path.append(os.path.join(os.path.dirname(__file__), "grpc"))
import motion_server_pb2
import motion_server_pb2_grpc


class TextToStyleBertVits(object):
    """
    Style-Bert-VITS2を使用してテキストから音声を生成するクラス。
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: str = "5000",
        motion_host: Optional[str] = "127.0.0.1",
        motion_port: Optional[str] = "50055",
    ) -> None:
        """クラスの初期化メソッド。
        Args:
            host (str, optional): Style-Bert-VITS2サーバーのホスト名。デフォルトは "127.0.0.1"。
            port (str, optional): Style-Bert-VITS2サーバーのポート番号。デフォルトは"5000"。
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
        self.model_id = 0
        self.length = 1.0
        self.style = "Neutral"
        self.style_weight = 1.0
        # 話者モデル名を指定
        self.set_param(model_name="jvnv-F1-jp")
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
                if (
                    self.sentence_end_flg
                    or (queue_start and time.time() - last_queue_time > self.sentence_end_timeout)
                ):
                    self.finished = True
                    queue_start = False
                    if self.motion_stub is not None:
                        print("Stop head control")
                        self.event.clear()
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

    def get_model_id_from_name(self, model_name: str) -> int:
        """
        モデル名からモデル番号を取得する。

        Args:
            model_name (str): モデル名。

        Returns:
            int: モデル番号。

        """
        headers = {"accept": "application/json"}
        address = "http://" + self.host + ":" + self.port + "/models/info"
        # GETリクエストを作成
        req = Request(address, headers=headers, method="GET")
        with urlopen(req) as res:
            model_info = res.read()
            model_info_json = json.loads(model_info)
            for key, details in model_info_json.items():
                if model_name == details["id2spk"]["0"]:
                    return key
        raise ValueError("Model name not found")

    def set_param(
        self,
        model_name: Optional[str] = None,
        model_id: Optional[int] = None,
        length: Optional[float] = None,
        style: Optional[str] = None,
        style_weight: Optional[float] = None,
    ) -> None:
        """
        音声合成のパラメータを設定する。

        Args:
            model_name (str, optional): Style-Bert-VITS2のモデル名。デフォルトはNone。
            model_id (int, optional): Style-Bert-VITS2のモデル番号。デフォルトはNone。
            length (float, optional): 音声の再生速度。大きくする程読み上げ速度が遅くなる。デフォルトはNone。
            style (str, optional): 音声の感情スタイル。デフォルトはNone。
            style_weight (float, optional): 音声の感情スタイルの重み。値が大きいほど感情の影響が大きくなる。デフォルトはNone。

        """
        if model_name is not None:
            self.model_id = self.get_model_id_from_name(model_name)
        elif model_id is not None:
            self.model_id = model_id
        if length is not None:
            self.length = length
        if style is not None:
            self.style = style
        if style_weight is not None:
            self.style_weight = style_weight

    def post_synthesis(
        self,
        text: str,
    ) -> Optional[bytes]:
        """
        Style-Bert-VITS2サーバーに音声合成要求を送信し、合成された音声データを取得する。

        Args:
            text (str): 音声合成対象のテキスト。

        Returns:
            Any: 音声合成クエリの応答。

        """
        if len(text.strip()) <= 0:
            return None
        headers = {"accept": "audio/wav"}
        params = {
            "text": text,
            "model_id": self.model_id,
            "length": self.length,
            "style": self.style,
            "style_weight": self.style_weight,
        }
        address = (
            "http://" + self.host + ":" + self.port + "/voice" + "?" + urlencode(params)
        )
        # GETリクエストを作成
        req = Request(address, headers=headers, method="GET")
        with urlopen(req) as res:
            return res.read()

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
                print(self.tilt_rate)
                stream.write(data)
                data = wr.readframes(chunk)
            time.sleep(0.2)
            stream.close()
        p.terminate()

    def text_to_voice(self, text: str) -> None:
        """
        テキストから音声を合成して再生する。

        Args:
            text (str): 音声合成対象のテキスト。

        """
        wav = self.post_synthesis(text)
        if wav is not None:
            print(f"[Play] {text}")
            self.play_wav(wav)

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
            print(f"tilt_rate: {self.tilt_rate}, prev_tilt_rate: {prev_tilt_rate}")
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
            print("Start head control")
            self.event.set()
