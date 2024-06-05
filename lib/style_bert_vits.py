import io
import json
import time
import wave
from queue import Queue
from threading import Thread
from typing import Any

import pyaudio
import requests

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
            while not self.finished:
                time.sleep(0.01)

    def wait_finish(self) -> None:
        """
        音声合成が完了するまで待機するループ関数。

        """
        while not self.finished:
            time.sleep(0.01)

    def post_audio_query(
        self,
        text: str,
        model_id: int = 0,
        speaker_id: int = 0,
        length: float = 1.0,
        style: str = "Neutral",
    ) -> Any:
        """Style-Bert-VITS2サーバーに音声合成クエリを送信する。

        Args:
            text (str): 音声合成対象のテキスト。
            model_id (int, optional): Style-Bert-VITS2のモデル番号。デフォルトは0。
            speaker_id (int, optional): Style-Bert-VITS2の話者番号。デフォルトは0。
            length (float, optional): 音声の再生速度。大きくする程読み上げ速度が遅くなる。デフォルトは1.0。
            style (str, optional): 音声の感情スタイル。"Neutral","Angry","Disgust","Fear","Happy","Sad","Surprise"が選択可能。デフォルトは"Neutral"。

        Returns:
            Any: 音声合成クエリの応答。

        """
        params = {
            "text": text,
            "model_id": model_id,
            "speaker_id": speaker_id,
            "length": length,
            "style": style
        }
        address = "http://" + self.host + ":" + self.port + "/voice"
        res = requests.post(address, params=params)
        return res.json()

    def post_synthesis(
        self,
        audio_query_response: dict,
    ) -> bytes:
        """
        Style-Bert-VITS2サーバーに音声合成要求を送信し、合成された音声データを取得する。

        Args:
            audio_query_response (dict): 音声合成クエリの応答。

        Returns:
            bytes: 合成された音声データ。
        """
        params = {"speaker": 8}
        headers = {"content-type": "application/json"}
        audio_query_response_json = json.dumps(audio_query_response)
        address = "http://" + self.host + ":" + self.port + "/synthesis"
        res = requests.post(
            address, data=audio_query_response_json, params=params, headers=headers
        )
        return res.content

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
        res = self.post_audio_query(text)
        wav = self.post_synthesis(res)
        self.play_wav(wav)
