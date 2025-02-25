import base64
import copy
import json
import os
import sys
import threading
from typing import Generator, List, Optional, Tuple, Union

import anthropic
import cv2
import grpc
import numpy as np
import openai
from google import genai
from google.genai import types
from google.genai.types import Content, Part
from gpt_stream_parser import force_parse_json

from .conf import ANTHROPIC_APIKEY, GEMINI_APIKEY

sys.path.append(os.path.join(os.path.dirname(__file__), "grpc"))
import motion_server_pb2
import motion_server_pb2_grpc


class ChatStreamAkari(object):
    """
    ChatGPTやClaude3を使用して会話を行うためのクラス。
    """

    def __init__(
        self, motion_host: str = "127.0.0.1", motion_port: str = "50055"
    ) -> None:
        """クラスの初期化メソッド。

        Args:
            motion_host (str, optional): モーションサーバーのホスト名。デフォルトは"127.0.0.1"。
            motion_port (str, optional): モーションサーバーのポート番号。デフォルトは"50055"。

        """
        motion_channel = grpc.insecure_channel(motion_host + ":" + motion_port)
        self.motion_stub = motion_server_pb2_grpc.MotionServerServiceStub(
            motion_channel
        )
        self.anthropic_client = None
        if ANTHROPIC_APIKEY is not None:
            self.anthropic_client = anthropic.Anthropic(
                api_key=ANTHROPIC_APIKEY,
            )
        if GEMINI_APIKEY is not None:
            self.gemini_client = genai.Client(api_key=GEMINI_APIKEY)
        self.last_char = ["、", "。", "！", "!", "?", "？", "\n", "}"]
        self.openai_model_name = [
            "gpt-4o",
            "gpt-4o-2024-11-20",
            "gpt-4o-2024-08-06",
            "gpt-4o-2024-05-13",
            "chatgpt-4o-latest",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4-turbo-2024-04-09",
            "gpt-4-0125-preview",
            "gpt-4-turbo-preview",
            "gpt-4-1106-preview",
            "gpt-4",
            "gpt-4-0613",
            "gpt-4-32k",
            "gpt-4-32k-0613",
            "gpt-3.5-turbo-0125",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-1106",
            "gpt-3.5-turbo-instruct",
        ]
        self.openai_vision_model_name = [
            "gpt-4o",
            "gpt-4o-2024-08-06",
            "gpt-4o-2024-05-13",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4-turbo-2024-04-09",
            "gpt-4-vision-preview",
            "gpt-4-1106-vision-preview",
        ]
        self.anthropic_model_name = [
            "claude-3-7-sonnet-latest",
            "claude-3-7-sonnet-20250219",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-latest",
            "claude-3-5-sonnet-20240620",
            "claude-3-5-haiku-20241022",
            "claude-3-5-haiku-latest",
            "claude-3-haiku-20240307",
            "claude-3-opus-20240229",
            "claude-3-opus-latest",
            "claude-3-sonnet-20240229",
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2",
        ]
        self.gemini_model_name = [
            "gemini-2.0-pro-exp",
            "gemini-2.0-pro-exp-02-05",
            "gemini-2.0-flash",
            "gemini-2.0-flash-001",
            "gemini-2.0-flash-lite-preview-02-05",
            "gemini-2.0-flash-exp",
            "gemini-2.0-flash-thinking-exp-01-21",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b",
        ]

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

    def cv_to_base64(self, image: np.ndarray) -> str:
        """OpenCV画像をbase64エンコードした文字列に変換する
        Args:
            image (np.ndarray): OpenCV画像データ

        Returns:
            str: base64エンコードされた画像データ

        """
        _, encoded = cv2.imencode(".jpg", image)
        return base64.b64encode(encoded).decode("ascii")

    def create_message(self, text: str, role: str = "user") -> str:
        """送信用メッセージを作成する
        Args:
            text (str): メッセージ内容
            role (str): メッセージの役割 (user または system)
        Returns:
            str: 作成したメッセージ

        """
        message = {"role": role, "content": text}
        return message

    def create_vision_message(
        self,
        text: str,
        image: Union[np.ndarray, List[np.ndarray]],
        model: str = None,  # type: ignore
        image_width: Optional[int] = None,
        image_height: Optional[int] = None,
    ) -> str:
        """画像付きメッセージを作成する(GPTの形式)

        Args:
            text (str): メッセージのテキスト部分
            image (np.ndarray または List[np.ndarray]): 画像データ
            model (str): 現在は使用しない引数 (デフォルト: None)
            image_width (int): 画像の幅 (デフォルト: 480)
            image_height (int): 画像の高さ (デフォルト: 270)
        Returns:
            str: 作成した画像付きメッセージ

        """
        image_list = []
        if isinstance(image, list):
            image_list = image
        else:
            image_list.append(image)
        message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": text,
                },
            ],
        }
        for image in image_list:
            if image_width is not None and image_height is not None:
                image = cv2.resize(image, (image_width, image_height))
            base64_image = self.cv_to_base64(image)
            url = f"data:image/jpeg;base64,{base64_image}"
            vision_message = {
                "type": "image_url",
                "image_url": {
                    "url": url,
                },
            }
            message["content"].append(vision_message)
        return message

    def convert_messages_from_gpt_to_anthropic(
        self, messages: list
    ) -> Tuple[str, list]:
        """GPTのメッセージをAnthropicのメッセージに変換する

        Args:
            messages (list): GPTのメッセージリスト
        Returns:
            Tuple(str, list): システムメッセージ, ユーザメッセージリスト

        """
        user_messages = []
        for message in messages:
            if "content" in message and isinstance(message["content"], list):
                for content in message["content"]:
                    if content["type"] == "image_url":
                        content["type"] = "image"
                        image_data = content["image_url"]["url"]
                        if image_data.startswith("data:image/jpeg;base64,"):
                            image_data = image_data[len("data:image/jpeg;base64,") :]
                        content["source"] = {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_data,
                        }
                        del content["image_url"]
            if message["role"] == "system":
                system_message = message["content"]
            elif message["role"] == "model":
                message["role"] = "assistant"
            else:
                user_messages.append(message)
        return system_message, user_messages

    def convert_messages_from_gpt_to_gemini(
        self, messages: list
    ) -> Tuple[str, list, dict]:
        """GPTのメッセージをGeminiのメッセージに変換する

        Args:
            messages (list): GPTのメッセージリスト
        Returns:
            Tuple(str, list, dict): システムメッセージ, メッセージ履歴, ユーザメッセージ
        """
        system_instruction = ""
        history = []

        # システムメッセージの取得と最後のユーザーメッセージを除外
        messages_for_history = []
        cur_message = None

        for message in messages:
            if message["role"] == "system":
                system_instruction = message["content"]
            elif message == messages[-1]:
                cur_message = message
            else:
                messages_for_history.append(message)

        if cur_message is None or cur_message["role"] != "user":
            raise ValueError("The last message must be user message.")

        # 履歴メッセージの変換
        for message in messages_for_history:
            parts = []
            if isinstance(message["content"], str):
                parts = [Part.from_text(text=message["content"])]
            elif isinstance(message["content"], list):
                text = ""
                for content in message["content"]:
                    if content["type"] == "text":
                        text = content["text"]
                    elif content["type"] == "image_url":
                        image_data = content["image_url"]["url"]
                        if image_data.startswith("data:image/jpeg;base64,"):
                            image_data = image_data[len("data:image/jpeg;base64,") :]
                        parts.append(
                            Part.from_bytes(
                                data=base64.b64decode(image_data),
                                mime_type="image/jpeg",
                            )
                        )
                if text:
                    parts.insert(0, Part.from_text(text=text))

            if parts:
                role = "model" if message["role"] == "assistant" else message["role"]
                history.append(Content(role=role, parts=parts))

        # 現在のメッセージの変換
        cur_parts = []
        if isinstance(cur_message["content"], str):
            cur_parts = [Part.from_text(text=cur_message["content"])]
        elif isinstance(cur_message["content"], list):
            text = ""
            for content in cur_message["content"]:
                if content["type"] == "text":
                    text = content["text"]
                elif content["type"] == "image_url":
                    image_data = content["image_url"]["url"]
                    if image_data.startswith("data:image/jpeg;base64,"):
                        image_data = image_data[len("data:image/jpeg;base64,") :]
                    cur_parts.append(
                        Part.from_bytes(
                            data=base64.b64decode(image_data), mime_type="image/jpeg"
                        )
                    )
            if text:
                cur_parts.insert(0, Part.from_text(text=text))

        role = "model" if cur_message["role"] == "assistant" else cur_message["role"]
        cur_message["contents"] = Content(role=role, parts=cur_parts)
        del cur_message["content"]
        del cur_message["role"]
        return system_instruction, history, cur_message

    def chat_gpt(
        self,
        messages: list,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        stream_per_sentence: bool = True,
    ) -> Generator[str, None, None]:
        """ChatGPTを使用して会話を行う

        Args:
            messages (list): 会話のメッセージ
            model (str): 使用するモデル名 (デフォルト: "gpt-4o")
            temperature (float): ChatGPTのtemperatureパラメータ (デフォルト: 0.7)
            stream_per_sentence (bool): 1文ごとにストリーミングするかどうか (デフォルト: True)
        Returns:
            Generator[str, None, None]): 会話の返答を順次生成する

        """
        result = None
        for message in messages:
            if message["role"] == "model":
                message["role"] = "assistant"
        result = openai.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1024,
            n=1,
            stream=True,
            temperature=temperature,
        )
        full_response = ""
        real_time_response = ""
        for chunk in result:
            text = chunk.choices[0].delta.content
            if text is None:
                pass
            else:
                full_response += text
                real_time_response += text
                if stream_per_sentence:
                    for index, char in enumerate(real_time_response):
                        if char in self.last_char:
                            pos = index + 1  # 区切り位置
                            sentence = real_time_response[:pos]  # 1文の区切り
                            real_time_response = real_time_response[pos:]  # 残りの部分
                            # 1文完成ごとにテキストを読み上げる(遅延時間短縮のため)
                            if sentence != "":
                                yield sentence
                            break
                        else:
                            pass
                else:
                    yield text
        if stream_per_sentence and real_time_response != "":
            yield real_time_response

    def chat_anthropic(
        self,
        messages: list,
        model: str = "claude-3-7-sonnet-latest",
        temperature: float = 0.7,
        stream_per_sentence: bool = True,
    ) -> Generator[str, None, None]:
        """Claude3を使用して会話を行う

        Args:
            messages (list): 会話のメッセージ
            model (str): 使用するモデル名 (デフォルト: "claude-3-7-sonnet-latest")
            temperature (float): Claude3のtemperatureパラメータ (デフォルト: 0.7)
            stream_per_sentence (bool): 1文ごとにストリーミングするかどうか (デフォルト: True)
        Returns:
            Generator[str, None, None]): 会話の返答を順次生成する

        """
        # anthropicではsystemメッセージは引数として与えるので、メッセージから抜き出す
        system_message = ""
        user_messages = []
        system_message, user_messages = self.convert_messages_from_gpt_to_anthropic(
            copy.deepcopy(messages)
        )
        with self.anthropic_client.messages.stream(
            model=model,
            max_tokens=1024,
            temperature=temperature,
            messages=user_messages,
            system=system_message,
        ) as result:
            full_response = ""
            real_time_response = ""
            for text in result.text_stream:
                if text is None:
                    pass
                else:
                    full_response += text
                    real_time_response += text
                    if stream_per_sentence:
                        for index, char in enumerate(real_time_response):
                            if char in self.last_char:
                                pos = index + 1  # 区切り位置
                                sentence = real_time_response[:pos]  # 1文の区切り
                                real_time_response = real_time_response[pos:]  # 残りの部分
                                # 1文完成ごとにテキストを読み上げる(遅延時間短縮のため)
                                if sentence != "":
                                    yield sentence
                                break
                            else:
                                pass
                    else:
                        yield text
            if stream_per_sentence and real_time_response != "":
                yield real_time_response

    def chat_gemini(
        self,
        messages: list,
        model: str = "gemini-2.0-flash-001",
        temperature: float = 0.7,
        stream_per_sentence: bool = True,
    ) -> Generator[str, None, None]:
        """Geminiを使用して会話を行う

        Args:
            messages (list): 会話のメッセージ
            model (str): 使用するモデル名 (デフォルト: "gemini-2.0-flash-001")
            temperature (float): Geminiのtemperatureパラメータ (デフォルト: 0.7)
            stream_per_sentence (bool): 1文ごとにストリーミングするかどうか (デフォルト: True)
        Returns:
            Generator[str, None, None]): 会話の返答を順次生成する

        """
        if GEMINI_APIKEY is None:
            print("Gemini API key is not set.")
            return
        (
            system_instruction,
            history,
            cur_message,
        ) = self.convert_messages_from_gpt_to_gemini(copy.deepcopy(messages))
        chat = self.gemini_client.chats.create(
            model=model,
            history=history,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction, temperature=temperature
            ),
        )
        responses = chat.send_message_stream(cur_message["contents"])
        full_response = ""
        real_time_response = ""
        for response in responses:
            text = response.text
            if text is None:
                pass
            else:
                full_response += text
                real_time_response += text
                if stream_per_sentence:
                    for index, char in enumerate(real_time_response):
                        if char in self.last_char:
                            pos = index + 1  # 区切り位置
                            sentence = real_time_response[:pos]  # 1文の区切り
                            real_time_response = real_time_response[pos:]  # 残りの部分
                            # 1文完成ごとにテキストを読み上げる(遅延時間短縮のため)
                            if sentence != "":
                                yield sentence
                            break
                        else:
                            pass
                else:
                    yield text
        if stream_per_sentence and real_time_response != "":
            yield real_time_response

    def chat(
        self,
        messages: list,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        stream_per_sentence: bool = True,
    ) -> Generator[str, None, None]:
        """指定したモデルを使用して会話を行う

        Args:
            messages (list): 会話のメッセージリスト
            model (str): 使用するモデル名 (デフォルト: "gpt-4o")
            temperature (float): サンプリングの温度パラメータ (デフォルト: 0.7)
            stream_per_sentence (bool): 1文ごとにストリーミングするかどうか (デフォルト: True)
        Returns:
            Generator[str, None, None]): 会話の返答を順次生成する

        """
        if model in self.openai_model_name or model in self.openai_vision_model_name:
            yield from self.chat_gpt(
                messages=messages,
                model=model,
                temperature=temperature,
                stream_per_sentence=stream_per_sentence,
            )
        elif model in self.anthropic_model_name:
            if self.anthropic_client is None:
                print("Anthropic API key is not set.")
                return
            yield from self.chat_anthropic(
                messages=messages,
                model=model,
                temperature=temperature,
                stream_per_sentence=stream_per_sentence,
            )
        elif model in self.gemini_model_name:
            if GEMINI_APIKEY is None:
                print("Gemini API key is not set.")
                return
            yield from self.chat_gemini(
                messages=messages,
                model=model,
                temperature=temperature,
                stream_per_sentence=stream_per_sentence,
            )
        else:
            print(f"Model name {model} can't use for this function")
            return

    def chat_anthropic_thinking(
        self,
        messages: list,
        model: str = "claude-3-7-sonnet-latest",
        max_tokens: int = 64000,
        budget_tokents: int = 32000,
        stream_per_sentence: bool = True,
    ) -> Generator[str, None, None]:
        """Claudeを使用して拡張思考モードで会話を行う

        Args:
            messages (list): 会話のメッセージ
            model (str): 使用するモデル名 (デフォルト: ""claude-3-7-sonnet-latest")
            max_tokens (int): 1回のリクエストで生成する最大トークン数 (デフォルト: 64000)
            budget_tokents (int): 1回のリクエストで拡張思考に使用するトークン数 (デフォルト: 32000)
            stream_per_sentence (bool): 1文ごとにストリーミングするかどうか (デフォルト: True)
        Returns:
            Generator[str, None, None]): 会話の返答を順次生成する

        """
        # anthropicではsystemメッセージは引数として与えるので、メッセージから抜き出す
        system_message = ""
        user_messages = []
        system_message, user_messages = self.convert_messages_from_gpt_to_anthropic(
            copy.deepcopy(messages)
        )
        with self.anthropic_client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            temperature=1.0,  # thinkingではtemperatureは1.0固定
            thinking={"type": "enabled", "budget_tokens": budget_tokents},
            messages=user_messages,
            system=system_message,
        ) as result:
            full_response = ""
            real_time_response = ""
            for text in result.text_stream:
                if text is None:
                    pass
                else:
                    full_response += text
                    real_time_response += text
                    if stream_per_sentence:
                        for index, char in enumerate(real_time_response):
                            if char in self.last_char:
                                pos = index + 1  # 区切り位置
                                sentence = real_time_response[:pos]  # 1文の区切り
                                real_time_response = real_time_response[pos:]  # 残りの部分
                                # 1文完成ごとにテキストを読み上げる(遅延時間短縮のため)
                                if sentence != "":
                                    yield sentence
                                break
                            else:
                                pass
                    else:
                        yield text
            if stream_per_sentence and real_time_response != "":
                yield real_time_response

    def chat_thinking(
        self,
        messages: list,
        model: str = "claude-3-7-sonnet-latest",
        max_tokens: int = 64000,
        budget_tokents: int = 32000,
        stream_per_sentence: bool = True,
    ) -> Generator[str, None, None]:
        """指定したモデルを使用して、拡張思考を用いた会話を行う

        Args:
            messages (list): 会話のメッセージリスト
            model (str): 使用するモデル名 (デフォルト: "claude-3-7-sonnet-latest")
            max_tokens (int): 1回のリクエストで生成する最大トークン数 (デフォルト: 64000)
            budget_tokents (int): 1回のリクエストで拡張思考に使用するトークン数 (デフォルト: 32000)
            stream_per_sentence (bool): 1文ごとにストリーミングするかどうか (デフォルト: True)
        Returns:
            Generator[str, None, None]): 会話の返答を順次生成する

        """
        if model in self.anthropic_model_name:
            if self.anthropic_client is None:
                print("Anthropic API key is not set.")
                return
            yield from self.chat_anthropic_thinking(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                budget_tokents=budget_tokents,
                stream_per_sentence=stream_per_sentence,
            )
        else:
            print(f"Model name {model} can't use for this function")
            return

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
        result = openai.chat.completions.create(
            model=model,
            messages=messages,
            n=1,
            temperature=temperature,
            functions=[
                {
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
        model: str = "gemini-2.0-flash-001",
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
        if GEMINI_APIKEY is None:
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
            if GEMINI_APIKEY is None:
                print("Gemini API key is not set.")
                return
            yield from self.chat_and_motion_gemini(
                messages=messages, model=model, temperature=temperature
            )
        else:
            print(f"Model name {model} can't use for this function")
            return
