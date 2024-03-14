import json
import os
import sys
from typing import Generator

import openai
from gpt_stream_parser import force_parse_json

from .chat_akari import ChatStreamAkari

sys.path.append(os.path.join(os.path.dirname(__file__), "grpc"))
import motion_server_pb2


class ChatStreamAkariGrpc(ChatStreamAkari):
    """ChatGPTやClaude3を使用して会話を行うためのクラス。

    """

    def __init__(
        self, motion_host: str = "127.0.0.1", motion_port: str = "50055"
    ) -> None:
        """クラスの初期化メソッド。

        Args:
            motion_host (str, optional): モーションサーバーのホスト名。デフォルトは"127.0.0.1"。
            motion_port (str, optional): モーションサーバーのポート番号。デフォルトは"50055"。

        """
        super().__init__(motion_host, motion_port)
        self.cur_motion_name = ""

    def send_reserved_motion(self) -> bool:
        """予約されたモーションを送信するメソッド。

        Returns:
            bool: モーションが送信されたかどうかを示すブール値。

        """
        print(f"send motion {self.cur_motion_name}")
        if self.cur_motion_name == "":
            self.motion_stub.ClearMotion(motion_server_pb2.ClearMotionRequest())
            return False
        try:
            self.motion_stub.SetMotion(
                motion_server_pb2.SetMotionRequest(
                    name=self.cur_motion_name, priority=3, repeat=False, clear=True
                )
            )
            self.cur_motion_name = ""
        except BaseException:
            print("setMotion error!")
            return False
        return True

    def chat_and_motion_gpt(
        self, messages: list, model: str = "gpt-4", temperature: float = 0.7
    ) -> Generator[str, None, None]:
        """ChatGPTを使用してチャットとモーションを処理するメソッド。

        Args:
            messages (list): チャットメッセージのリスト。
            model (str, optional): 使用するOpenAI GPTモデル。デフォルトは"gpt-4"。
            temperature (float, optional): サンプリング温度。デフォルトは0.7。

        Yields:
            str: チャット応答のジェネレータ。

        """
        result = openai.chat.completions.create(
            model=model,
            messages=messages,
            n=1,
            temperature=temperature,
            functions=[
                {
                    "name": "reply_with_motion_",
                    "description": "ユーザのメッセージに対する回答と、回答の感情に近い動作を一つ選択します。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "motion": {
                                "type": "string",
                                "description": "動作",
                                "enum": [
                                    "肯定する",
                                    "否定する",
                                    "おじぎ",
                                    "喜ぶ",
                                    "笑う",
                                    "落ち込む",
                                    "うんざりする",
                                    "眠る",
                                ],
                            },
                            "talk": {
                                "type": "string",
                                "description": "回答",
                                "enum": [
                                    "えーと。",
                                    "はい。",
                                    "うーん。",
                                    "いいえ。",
                                    "そうですね。",
                                    "こんにちは。",
                                    "ありがとうございます。",
                                    "なるほど。",
                                    "まあ。",
                                    "確かに。",
                                ],
                            },
                        },
                        "required": ["motion", "talk"],
                    },
                }
            ],
            function_call={"name": "reply_with_motion_"},
            stream=True,
            stop=None,
        )
        full_response = ""
        real_time_response = ""
        sentence_index = 0
        get_motion = False
        for chunk in result:
            delta = chunk.choices[0].delta
            if delta.function_call is not None:
                if delta.function_call.arguments is not None:
                    full_response += chunk.choices[0].delta.function_call.arguments
                    try:
                        data_json = json.loads(full_response)
                        found_last_char = False
                        for char in self.last_char:
                            if real_time_response[-1].find(char) >= 0:
                                found_last_char = True
                        if not found_last_char:
                            data_json["talk"] = data_json["talk"] + "。"
                    except BaseException:
                        data_json = force_parse_json(full_response)
                    if data_json is not None:
                        if "talk" in data_json:
                            if not get_motion and "motion" in data_json:
                                get_motion = True
                                motion = data_json["motion"]
                                if motion == "肯定する":
                                    key = "agree"
                                elif motion == "否定する":
                                    key = "swing"
                                elif motion == "おじぎ":
                                    key = "bow"
                                elif motion == "喜ぶ":
                                    key = "happy"
                                elif motion == "笑う":
                                    key = "lough"
                                elif motion == "落ち込む":
                                    key = "depressed"
                                elif motion == "うんざりする":
                                    key = "amazed"
                                elif motion == "眠る":
                                    key = "sleep"
                                elif motion == "ぼんやりする":
                                    key = "lookup"
                                print("motion: " + motion)
                                self.cur_motion_name = key
                            real_time_response = str(data_json["talk"])
                            for char in self.last_char:
                                pos = real_time_response[sentence_index:].find(char)
                                if pos >= 0:
                                    sentence = real_time_response[
                                        sentence_index : sentence_index + pos + 1
                                    ]
                                    sentence_index += pos + 1
                                    yield sentence
                                    break

    def chat_and_motion_anthropic(
        self,
        messages: list,
        model: str = "claude-3-sonnet-20240229",
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """Anthropicモデルを使用してチャットとモーションを処理するメソッド。

        Args:
            messages (list): チャットメッセージのリスト。
            model (str, optional): 使用するAnthropicモデル。デフォルトは"claude-3-sonnet-20240229"。
            temperature (float, optional): サンプリング温度。デフォルトは0.7。

        Yields:
            str: チャット応答のジェネレータ。

        """
        system_message = ""
        user_messages = []
        for message in messages:
            if message["role"] == "system":
                system_message = message["content"]
            else:
                user_messages.append(message)
        # 最後の1文を動作と文章のJSON形式出力指定に修正
        user_messages[-1][
            "content"
        ] = f"「{user_messages[-1]['content']}」に対する返答を下記のJSON形式で出力してください。{{\"motion\": 次の()内から動作を一つだけ選択して返す(\"肯定する\",\"否定する\",\"おじぎ\",\"喜ぶ\",\"笑う\",\"落ち込む\",\"うんざりする\",\"眠る\"), \"talk\": 次の()内から返答を一つだけ選択して返す(\"えーと。\",\"はい。\",\"うーん。\",\"いいえ。\",\"そうですね。\",\"こんにちは。\",\"ありがとうございます。\",\"なるほど。\",\"まあ。\",\"確かに。\")}}"
        with self.anthropic_client.messages.stream(
            model=model,
            max_tokens=1000,
            temperature=temperature,
            messages=user_messages,
            system=system_message,
        ) as result:
            full_response = ""
            real_time_response = ""
            sentence_index = 0
            get_motion = False
            for text in result.text_stream:
                if text is None:
                    pass
                else:
                    full_response += text
                    real_time_response += text
                    try:
                        data_json = json.loads(full_response)
                        found_last_char = False
                        for char in self.last_char:
                            if real_time_response[-1].find(char) >= 0:
                                found_last_char = True
                        if not found_last_char:
                            data_json["talk"] = data_json["talk"] + "。"
                    except BaseException:
                        data_json = force_parse_json(full_response)
                    if data_json is not None:
                        if "talk" in data_json:
                            if not get_motion and "motion" in data_json:
                                get_motion = True
                                motion = data_json["motion"]
                                if motion == "肯定する":
                                    key = "agree"
                                elif motion == "否定する":
                                    key = "swing"
                                elif motion == "おじぎ":
                                    key = "bow"
                                elif motion == "喜ぶ":
                                    key = "happy"
                                elif motion == "笑う":
                                    key = "lough"
                                elif motion == "落ち込む":
                                    key = "depressed"
                                elif motion == "うんざりする":
                                    key = "amazed"
                                elif motion == "眠る":
                                    key = "sleep"
                                elif motion == "ぼんやりする":
                                    key = "lookup"
                                print("motion: " + motion)
                                self.cur_motion_name = key
                            real_time_response = str(data_json["talk"])
                            for char in self.last_char:
                                pos = real_time_response[sentence_index:].find(char)
                                if pos >= 0:
                                    sentence = real_time_response[
                                        sentence_index : sentence_index + pos + 1
                                    ]
                                    sentence_index += pos + 1
                                    yield sentence
                                    break
