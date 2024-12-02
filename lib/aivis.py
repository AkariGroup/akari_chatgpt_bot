import json
from typing import Any, Optional

import requests
from lib.text_to_voice import TextToVoice


class TextToAivis(TextToVoice):
    """
    Aivisを使用してテキストから音声を生成するクラス。
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: str = "10101",
        motion_host: Optional[str] = "127.0.0.1",
        motion_port: Optional[str] = "50055",
    ) -> None:
        """クラスの初期化メソッド。
        Args:
            host (str, optional): Aivisサーバーのホスト名。デフォルトは "127.0.0.1"。
            port (str, optional): Aivisサーバーのポート番号。デフォルトは "10101"。
            motion_host (str, optional): モーションサーバーのホスト名。デフォルトは"127.0.0.1"。
            motion_port (str, optional): モーションサーバーのポート番号。デフォルトは"50055"。

        """
        super().__init__(
            host=host, port=port, motion_host=motion_host, motion_port=motion_port
        )
        # デフォルトのspeakerはAnneli
        self.speaker = "Anneli"
        self.style = "ノーマル"
        self.speed_scale = 1.0
        self.speaker_id = self.get_speaker_id(self.speaker, self.style)

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
