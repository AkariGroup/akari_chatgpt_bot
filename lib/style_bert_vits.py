import json
from typing import Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from lib.text_to_voice import TextToVoice


class TextToStyleBertVits(TextToVoice):
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
        super().__init__(host, port, motion_host, motion_port)
        self.model_id = 0
        self.length = 1.0
        self.style = "Neutral"
        self.style_weight = 1.0
        # 話者モデル名を指定
        self.set_param(model_name="jvnv-F1-jp")

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
