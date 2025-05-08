import copy
import json
import os
import sys
import threading
from typing import Generator

import grpc
from google.genai import types
from gpt_stream_parser import force_parse_json

from .chat import ChatStream

sys.path.append(os.path.join(os.path.dirname(__file__), "grpc"))
import motion_server_pb2
import motion_server_pb2_grpc


class ChatStreamAkari(ChatStream):
    """
    LLMを使用して会話とAKARIのモーション選択を行うためのクラス。
    """

    def __init__(
        self, motion_host: str = "127.0.0.1", motion_port: str = "50055"
    ) -> None:
        """クラスの初期化メソッド。

        Args:
            motion_host (str, optional): モーションサーバーのホスト名。デフォルトは"127.0.0.1"。
            motion_port (str, optional): モーションサーバーのポート番号。デフォルトは"50055"。

        """
        super().__init__()
        motion_channel = grpc.insecure_channel(motion_host + ":" + motion_port)
        self.motion_stub = motion_server_pb2_grpc.MotionServerServiceStub(
            motion_channel
        )

    def send_motion(self, name: str) -> None:
        """motion serverに動作を送信する

        Args:
            name (str): 動作名

        """
        try:
            self.motion_stub.SetMotion(
                motion_server_pb2.SetMotionRequest(
                    name=name, priority=3, repeat=False, clear=True
                )
            )
        except BaseException:
            print("send error!")
            pass

    def chat_and_motion_gpt(
        self,
        messages: list,
        model: str = "gpt-4o",
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """ChatGPTを使用して会話を行い、会話の内容に応じた動作も生成する

        Args:
            messages (list): メッセージリスト
            model (str): 使用するモデル名 (デフォルト: "gpt-4o")
            temperature (float): ChatGPTのtemperatureパラメータ (デフォルト: 0.7)
        Returns:
            Generator[str, None, None]): 会話の返答を順次生成する

        """
        if self.openai_client is None:
            raise ValueError("OpenAI API key is not set.")
        if model in self.openai_flagship_model_name:
            raise ValueError("Flagship model is not supported.")
        result = self.openai_client.responses.create(
            model=model,
            input=messages,
            temperature=temperature,
            tools=[
                {
                    "type": "function",
                    "name": "reply_with_motion_",
                    "description": "ユーザのメッセージに対する回答と、回答の感情に近い動作を一つ選択します",
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
                            },
                        },
                        "required": ["motion", "talk"],
                    },
                }
            ],
            tool_choice={
                "type": "function",
                "name": "reply_with_motion_",
            },
            stream=True,
        )
        full_response = ""
        real_time_response = ""
        sentence_index = 0
        get_motion = False
        for chunk in result:
            if chunk.type != "response.function_call_arguments.delta":
                continue
            full_response += chunk.delta
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
                        motion_thread = threading.Thread(
                            target=self.send_motion, args=(key,)
                        )
                        motion_thread.start()
                    real_time_response = str(data_json["talk"])
                    for char in self.last_char:
                        pos = real_time_response[sentence_index:].find(char)
                        if pos >= 0:
                            sentence = real_time_response[
                                sentence_index : sentence_index + pos + 1
                            ]
                            sentence_index += pos + 1
                            if sentence != "":
                                yield sentence
                            # break

    def chat_and_motion_anthropic(
        self,
        messages: list,
        model: str = "claude-3-sonnet-20240229",
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """Claude3を使用して会話を行い、会話の内容に応じた動作も生成する

        Args:
            messages (list): メッセージリスト
            model (str): 使用するモデル名 (デフォルト:"claude-3-sonnet-20240229")
            temperature (float): Claude3のtemperatureパラメータ (デフォルト: 0.7)
        Returns:
            Generator[str, None, None]): 会話の返答を順次生成する

        """
        system_message = ""
        user_messages = []
        for message in messages:
            if message["role"] == "system":
                system_message = message["content"]
            else:
                user_messages.append(message)
        # 最後の1文を動作と文章のJSON形式出力指定に修正
        motion_json_format = (
            f"「{user_messages[-1]['content']}」に対する返答を下記のJSON形式で出力してください。"
            '{"motion": 次の()内から動作を一つ選択("肯定する","否定する","おじぎ",'
            '"喜ぶ","笑う","落ち込む","うんざりする","眠る"), "talk": 会話の返答'
            "}"
        )
        user_messages[-1]["content"] = motion_json_format
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
                        full_response_json = full_response[
                            full_response.find("{") : full_response.rfind("}") + 1
                        ]
                        data_json = force_parse_json(full_response_json)
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
                                motion_thread = threading.Thread(
                                    target=self.send_motion, args=(key,)
                                )
                                motion_thread.start()
                            real_time_response = str(data_json["talk"])
                            for char in self.last_char:
                                pos = real_time_response[sentence_index:].find(char)
                                if pos >= 0:
                                    sentence = real_time_response[
                                        sentence_index : sentence_index + pos + 1
                                    ]
                                    sentence_index += pos + 1
                                    if sentence != "":
                                        yield sentence
                                    # break

    def chat_and_motion_gemini(
        self,
        messages: list,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """ChatGPTを使用して会話を行い、会話の内容に応じた動作も生成する

        Args:
            messages (list): メッセージリスト
            model (str): 使用するモデル名 (デフォルト: "gemini-2.0-flash")
            temperature (float): ChatGPTのtemperatureパラメータ (デフォルト: 0.7)
        Returns:
            Generator[str, None, None]): 会話の返答を順次生成する

        """
        if self.gemini_client is None:
            print("Gemini API key is not set.")
            return
        new_messages = copy.deepcopy(messages)
        new_messages[-1]["content"] = (
            f"「{new_messages[-1]['content']}」に対する返答を下記のJSON形式で出力してください。"
            '{"motion": 次の()内から動作を一つ選択("肯定する","否定する","おじぎ",'
            '"喜ぶ","笑う","落ち込む","うんざりする","眠る"), "talk": 会話の返答'
            "}"
        )
        (
            system_instruction,
            history,
            cur_message,
        ) = self.convert_messages_from_gpt_to_gemini(new_messages)

        chat = self.gemini_client.chats.create(
            model=model,
            history=history,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction, temperature=0.5
            ),
        )
        responses = chat.send_message_stream(cur_message["contents"])
        full_response = ""
        real_time_response = ""
        sentence_index = 0
        get_motion = False
        for response in responses:
            text = response.text
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
                    full_response_json = full_response[
                        full_response.find("{") : full_response.rfind("}") + 1
                    ]
                    data_json = force_parse_json(full_response_json)
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
                            motion_thread = threading.Thread(
                                target=self.send_motion, args=(key,)
                            )
                            motion_thread.start()
                        real_time_response = str(data_json["talk"])
                        for char in self.last_char:
                            pos = real_time_response[sentence_index:].find(char)
                            if pos >= 0:
                                sentence = real_time_response[
                                    sentence_index : sentence_index + pos + 1
                                ]
                                sentence_index += pos + 1
                                if sentence != "":
                                    yield sentence

    def chat_and_motion(
        self,
        messages: list,
        model: str = "gpt-4o",
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """指定したモデルを使用して会話を行い、会話の内容に応じた動作も生成する

        Args:
            messages (list): 会話のメッセージ
            model (str): 使用するモデル名 (デフォルト: "gpt-4o")
            temperature (float): temperatureパラメータ (デフォルト: 0.7)
        Returns:
            Generator[str, None, None]): 返答を順次生成する

        """
        if model in self.openai_model_name:
            yield from self.chat_and_motion_gpt(
                messages=messages, model=model, temperature=temperature
            )
        elif model in self.anthropic_model_name:
            if self.anthropic_client is None:
                print("Anthropic API key is not set.")
                return
            yield from self.chat_and_motion_anthropic(
                messages=messages, model=model, temperature=temperature
            )
        elif model in self.gemini_model_name:
            if self.gemini_client is None:
                print("Gemini API key is not set.")
                return
            yield from self.chat_and_motion_gemini(
                messages=messages, model=model, temperature=temperature
            )
        else:
            print(f"Model name {model} can't use for this function")
            return
