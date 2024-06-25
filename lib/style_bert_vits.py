import io
import json
import time
import wave
from queue import Queue
from threading import Thread
from typing import Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pyaudio

from .err_handler import ignoreStderr


class TextToStyleBertVits(object):
    """
    Style-Bert-VITS2を使用してテキストから音声を生成するクラス。
    """

    def __init__(self, host: str = "127.0.0.1", port: str = "5000") -> None:
        """クラスの初期化メソッド。
        Args:
            host (str, optional): Style-Bert-VITS2サーバーのホスト名。デフォルトは "127.0.0.1"。
            port (str, optional): Style-Bert-VITS2サーバーのポート番号。デフォルトは"5000"。

        """
        self.queue: Queue[str] = Queue()
        self.host = host
        self.port = port
        self.play_flg = False
        self.finished = True
        self.voice_thread = Thread(target=self.text_to_voice_thread)
        self.voice_thread.start()
        self.model_id = 0
        self.length = 1.0
        self.style = "Neutral"
        self.style_weight = 1.0
        # 話者モデル名を指定
        self.set_param(model_name="jvnv-F1-jp")

    def __exit__(self) -> None:
        """音声合成スレッドを終了する。"""
        self.voice_thread.join()

    def text_to_voice_thread(self) -> None:
        """
        音声合成スレッドの実行関数。
        キューからテキストを取り出し、text_to_voice関数を呼び出す。

        """
        while True:
            if self.queue.qsize() > 0 and self.play_flg:
                text = self.queue.get()
                self.text_to_voice(text)
            if self.queue.qsize() == 0:
                self.finished = True

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
            self.play_flg = True
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
        if text == "":
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
            while data and self.play_flg:
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
            self.play_wav(wav)

    def is_playing(self) -> bool:
        """
        音声再生が実行中かどうかを返す。
        queueの中身が0かつ再生中の音声がなければFalseを返す。

        Returns:
            bool: 音声再生中の場合はTrue。

        """
        return self.finished
