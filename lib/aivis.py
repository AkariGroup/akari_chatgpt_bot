import io
import json
import time
import wave
from queue import Queue
from threading import Thread
from typing import Any, Optional

import pyaudio
import requests
from lib.en_to_jp import EnToJp

from .err_handler import ignoreStderr


class TextToAivis(object):
    """
    Aivisを使用してテキストから音声を生成するクラス。
    """

    def __init__(self, host: str = "127.0.0.1", port: str = "10101") -> None:
        """クラスの初期化メソッド。
        Args:
            host (str, optional): Aivisサーバーのホスト名。デフォルトは "127.0.0.1"。
            port (str, optional): Aivisサーバーのポート番号。デフォルトは "10101"。

        """
        self.queue: Queue[str] = Queue()
        self.host = host
        self.port = port
        self.play_flg = False  # 音声再生を実行するフラグ
        self.finished = True  # 音声再生が完了したかどうかを示すフラグ
        self.sentence_end_flg = True  # 一文の終わりを示すフラグ
        self.sentence_end_timeout = 5.0  # 一文の終わりを判定するタイムアウト時間
        # デフォルトのspeakerはAnneli
        self.speaker = "Anneli"
        self.style = "ノーマル"
        self.speed_scale = 1.0
        self.voice_thread = Thread(target=self.text_to_voice_thread)
        self.voice_thread.start()
        self.en_to_jp = EnToJp()
        # print(self.get_speaker_names())
        # print(self.get_style_names(self.speaker))
        self.speaker_id = self.get_speaker_id(self.speaker, self.style)

    def __exit__(self) -> None:
        """音声合成スレッドを終了する。"""
        self.voice_thread.join()

    def sentence_end(self) -> None:
        self.sentence_end_flg = True

    def text_to_voice_thread(self) -> None:
        """
        音声合成スレッドの実行関数。
        キューからテキストを取り出し、text_to_voice関数を呼び出す。

        """
        last_queue_time = time.time()
        while True:
            if self.queue.qsize() > 0 and self.play_flg:
                last_queue_time = time.time()
                text = self.queue.get()
                # textに含まれる英語を極力かな変換する
                text = self.en_to_jp.text_to_kana(text, True, True, True)
                self.text_to_voice(text)
            if self.queue.qsize() == 0:
                # queueが空の状態でsentence_endが送られる、もしくはsentence_end_timeout秒経過した場合finishedにする。
                if (
                    self.sentence_end_flg
                    or time.time() - last_queue_time > self.sentence_end_timeout
                ):
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
        self.sentence_end_flg = False
        if blocking:
            self.wait_finish()

    def wait_finish(self) -> None:
        """
        音声合成が完了するまで待機するループ関数。

        """
        while not self.finished:
            time.sleep(0.01)

    def set_param(
        self,
        speaker: Optional[int] = None,
        style: Optional[str] = None,
        speed_scale: Optional[float] = None,
    ) -> None:
        """
        音声合成のパラメータを設定する。

        Args:
            speaker (Optional[int], optional): Aivisの話者番号。デフォルトはNone。
            speed_scale (Optional[float], optional): 音声の再生速度スケール。デフォルトはNone。

        """
        if speaker is not None:
            self.speaker = speaker
        if style is not None:
            self.style = style
        if speed_scale is not None:
            self.speed_scale = speed_scale
        self.speaker_id = self.get_speaker_id(self.speaker, self.style)

    def post_audio_query(
        self,
        text: str,
    ) -> Any:
        """Aivisサーバーに音声合成クエリを送信する。

        Args:
            text (str): 音声合成対象のテキスト。
            speaker (int, optional): Aivisの話者番号。デフォルトは8(春日部つむぎ)。
            speed_scale (float, optional): 音声の再生速度スケール。デフォルトは1.0。

        Returns:
            Any: 音声合成クエリの応答。

        """
        if len(text.strip()) <= 0:
            return None
        params = {
            "text": text,
            "speaker": self.speaker_id,
            "speedScale": self.speed_scale,
            "prePhonemeLength": 0,
            "postPhonemeLength": 0,
        }
        address = "http://" + self.host + ":" + self.port + "/audio_query"
        res = requests.post(address, params=params)
        return res.json()

    def post_synthesis(
        self,
        audio_query_response: dict,
    ) -> bytes:
        """
        Aivisサーバーに音声合成要求を送信し、合成された音声データを取得する。

        Args:
            audio_query_response (dict): 音声合成クエリの応答。

        Returns:
            bytes: 合成された音声データ。
        """
        params = {"speaker": self.speaker_id}
        headers = {"content-type": "application/json"}
        audio_query_response["speedScale"] = self.speed_scale
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
        if res is None:
            return
        wav = self.post_synthesis(res)
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

    def get_speaker(self) -> Any:
        """
        Aivisの話者情報を取得する。

        Returns:
            Any: Aivisの話者情報。
        """
        headers = {"content-type": "application/json"}
        address = "http://" + self.host + ":" + self.port + "/speakers"
        res = requests.get(address, headers=headers)
        return res.json()

    def get_speaker_names(self) -> Any:
        """
        Aivisの話者名を取得する。

        Returns:
            Any: Aivisの話者名。
        """
        speakers = self.get_speaker()
        speaker_names = []
        for speaker in speakers:
            speaker_names.append(speaker["name"])
        return speaker_names

    def get_style_names(self, speaker_name) -> Any:
        """
        Aivisの話者名から感情スタイル名を取得する。

        Args:
            speaker_name (str): 話者名。

        Returns:
            Any: 感情スタイル名。
        """
        speakers = self.get_speaker()
        for speaker in speakers:
            if speaker["name"] == speaker_name:
                style_names = []
                for style in speaker["styles"]:
                    style_names.append(style["name"])
                return style_names
            print(f"Speaker: {speaker_name} not found.")
        return None

    def get_speaker_id(self, speaker_name, style_name) -> Optional[int]:
        """
        Aivisの話者名から話者IDを取得する。

        Args:
            name (str): 話者名。
            style (str): 感情スタイル。

        Returns:
            int: 話者ID。
        """
        speakers = self.get_speaker()
        for speaker in speakers:
            if speaker["name"] == speaker_name:
                for style in speaker["styles"]:
                    if style["name"] == style_name:
                        return style["id"]
                print(f"Style: {style_name} not found in speaker: {speaker_name}.")
                return None
            print(f"Speaker: {speaker_name} not found.")
        return None
