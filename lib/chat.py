import base64
import copy
from typing import Any, Generator, Optional, Tuple, Union

import anthropic
import cv2
import numpy as np
from google import genai
from google.genai import types
from google.genai.types import Content, Part
from gpt_stream_parser import force_parse_json
from openai import OpenAI

from .conf import ANTHROPIC_APIKEY, GEMINI_APIKEY, OPENAI_APIKEY


class ChatStream(object):
    """
    LLMを使用してレスポンスを取得するためのクラス。
    """

    def __init__(self) -> None:
        """クラスの初期化メソッド。"""
        self.anthropic_client = None
        if ANTHROPIC_APIKEY is not None:
            self.anthropic_client = anthropic.Anthropic(
                api_key=ANTHROPIC_APIKEY,
            )
        self.openai_client = None
        if OPENAI_APIKEY is not None:
            self.openai_client = OpenAI(
                api_key=OPENAI_APIKEY,
            )
        self.gemini_client = None
        if GEMINI_APIKEY is not None:
            self.gemini_client = genai.Client(api_key=GEMINI_APIKEY)
        self.last_char = ["。", "！", "!", "?", "？", "\n", "}"]
        self.openai_flagship_model_name = [
            "o1",
            "o1-2024-12-17",
            "o1-mini",
            "o1-mini-2024-09-12",
            "o3",
            "o3-mini",
            "o3-mini-2025-01-31",
            "o4-mini",
            "o4-mini-2025-04-16",
            "o1-preview",
            "o1-preview-2024-09-12",
        ]
        self.openai_gpt5_model_name = [
            "gpt-5",
            "gpt-5-2025-08-07",
            "gpt-5-mini",
            "gpt-5-mini-2025-08-07",
            "gpt-5-nano",
            "gpt-5-nano-2025-08-07",
            "gpt-5-chat-latest",
        ]
        self.openai_model_name = [
            "gpt-4.5-preview",
            "gpt-4.5-preview-2025-02-27",
            "gpt-4.1",
            "gpt-4.1-2025-04-14",
            "gpt-4.1-mini",
            "gpt-4.1-mini-2025-04-14",
            "gpt-4.1-nano",
            "gpt-4.1-nano-2025-04-14",
            "gpt-4o",
            "gpt-4o-2024-11-20",
            "gpt-4o-2024-08-06",
            "gpt-4o-2024-05-13",
            "gpt-4o-search-preview",
            "gpt-4o-search-preview-2025-03-11",
            "gpt-4o-mini-search-preview",
            "gpt-4o-mini-search-preview-2025-03-11",
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
        self.anthropic_model_name = [
            "claude-opus-4-20250514",
            "claude-sonnet-4-20250514",
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
            "gemini-2.5-pro",
            "gemini-2.5-pro-preview-06-05",
            "gemini-2.5-pro-preview-05-06",
            "gemini-2.5-flash",
            "gemini-2.5-flash-preview-05-20",
            "gemini-2.5-flash-lite-preview-06-17",
            "gemini-2.0-pro-exp",
            "gemini-2.0-pro-exp-02-05",
            "gemini-2.0-flash",
            "gemini-2.0-flash-001",
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash-lite-001",
            "gemini-2.0-flash-lite-preview-02-05",
            "gemini-2.0-flash-exp",
            "gemini-2.0-flash-thinking-exp-01-21",
            "gemini-2.0-flash-thinking-exp",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b",
        ]

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
        image: Union[np.ndarray, list[np.ndarray], str, list[str]],
        model: Optional[str] = None,
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
                    "type": "input_text",
                    "text": text,
                },
            ],
        }
        for image in image_list:
            if isinstance(image, np.ndarray):
                if image_width is not None and image_height is not None:
                    image = cv2.resize(image, (image_width, image_height))
                image = self.cv_to_base64(image)
            url = f"data:image/jpeg;base64,{image}"
            vision_message = {
                "type": "input_image",
                "image_url": url,
            }
            message["content"].append(vision_message)
        return message

    def convert_messages_from_gpt_to_gpt_legacy(
        self, messages: list
    ) -> tuple[str, list]:
        """GPTのメッセージをGPT Legacyのメッセージに変換する

        Args:
            messages (list): GPTのメッセージリスト
        Returns:
            Tuple(str, list): システムメッセージ, ユーザメッセージリスト

        """
        for message in messages:
            if "content" in message and isinstance(message["content"], list):
                for content in message["content"]:
                    if content["type"] == "input_text":
                        content["type"] = "text"
                    elif content["type"] == "input_image":
                        content["type"] = "image_url"
                        image_data = content["image_url"]
                        del content["image_url"]
                        content["image_url"] = {}
                        content["image_url"]["url"] = image_data
        return messages

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
                    if content["type"] == "input_text":
                        content["type"] = "text"
                    elif content["type"] == "input_image":
                        content["type"] = "image"
                        image_data = content["image_url"]
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
                    if content["type"] == "input_text":
                        text = content["text"]
                    elif content["type"] == "input_image":
                        image_data = content["image_url"]
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
                if content["type"] == "input_text":
                    text = content["text"]
                elif content["type"] == "input_image":
                    image_data = content["image_url"]
                    if image_data.startswith("data:image/jpeg;base64,"):
                        image_data = image_data[len("data:image/jpeg;base64,") :]
                    cur_parts.append(
                        Part.from_bytes(
                            data=base64.b64decode(image_data), mime_type="image/jpeg"
                        )
                    )
            if text:
                cur_parts.insert(0, Part.from_text(text=text))
        return system_instruction, history, cur_parts

    def parse_output_stream_gpt(
        self, response: Any, stream_per_sentence: bool = True
    ) -> Generator[str, None, None]:
        """GPTのストリーム出力を解析してテキストを返す

        Args:
            result (Any): ストリーム出力
            stream_per_sentence (bool): 1文ごとにストリーミングするかどうか (デフォルト: True)
        Returns:
            Generator[str, None, None]): 会話の返答を順次生成する

        """
        full_response = ""
        real_time_response = ""
        for chunk in response:
            if chunk.type == "response.output_text.done":
                break
            if chunk.type != "response.output_text.delta":
                continue
            text = chunk.delta
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

    def parse_output_stream_gpt_legacy(
        self, response: Any, stream_per_sentence: bool = True
    ) -> Generator[str, None, None]:
        """GPT chat completions APIのストリーム出力を解析してテキストを返す

        Args:
            result (Any): ストリーム出力
            stream_per_sentence (bool): 1文ごとにストリーミングするかどうか (デフォルト: True)
        Returns:
            Generator[str, None, None]): 会話の返答を順次生成する

        """
        full_response = ""
        real_time_response = ""
        for chunk in response:
            if len(chunk.choices) == 0:
                continue
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

    def parse_output_stream_anthropic(
        self, responses: Any, stream_per_sentence: bool = True
    ) -> Generator[str, None, None]:
        """Anthropicのストリーム出力を解析してテキストを返す

        Args:
            responses (Any): Anthropicのストリーム出力
            stream_per_sentence (bool): 1文ごとにストリーミングするかどうか (デフォルト: True)
        Returns:
            Generator[str, None, None]): 会話の返答を順次生成する

        """
        full_response = ""
        real_time_response = ""
        for text in responses.text_stream:
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

    def parse_output_stream_gemini(
        self, responses: Any, stream_per_sentence: bool = True
    ) -> Generator[str, None, None]:
        """Geminiのストリーム出力を解析してテキストを返す

        Args:
            responses (Any): Geminiのストリーム出力
            stream_per_sentence (bool): 1文ごとにストリーミングするかどうか (デフォルト: True)
        Returns:
            Generator[str, None, None]): 会話の返答を順次生成する

        """
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

    def chat_gpt(
        self,
        messages: list,
        model: str = "gpt-4.1",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        verbosity: str = "low",
        reasoning_effort: str = "minimal",
        timeout: Optional[float] = None,
        stream_per_sentence: bool = True,
    ) -> Generator[str, None, None]:
        """ChatGPTを使用してレスポンスを取得する

        Args:
            messages (list): 会話のメッセージ
            model (str): 使用するモデル名 (デフォルト: "gpt-4.1")
            temperature (float): ChatGPTのtemperatureパラメータ (デフォルト: 0.7)
            max_tokens (int): 1回のリクエストで生成する最大トークン数 (デフォルト: 1024)
            verbosity (str): レスポンスの冗長性 ("low","medium", "high") (デフォルト: "low")
            reasoning_effort (str): 推論の努力レベル ("minimal", "low", "medium", "high") (デフォルト: "minimal")
            timeout (float): リクエストのタイムアウト時間 (デフォルト: None)
            stream_per_sentence (bool): 1文ごとにストリーミングするかどうか (デフォルト: True)
        Returns:
            Generator[str, None, None]): 会話の返答を順次生成する

        """
        if self.openai_client is None:
            raise ValueError("OpenAI API key is not set.")
        result = None
        messages = self.convert_messages_from_gpt_to_gpt_legacy(copy.deepcopy(messages))
        if model in self.openai_flagship_model_name:
            try:
                result = self.openai_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    timeout=timeout,
                    stream=True,
                    reasoning_effort=reasoning_effort,
                )
            except BaseException as e:
                print(f"OpenAIレスポンスエラー: {e}")
                raise (e)
        elif model in self.openai_gpt5_model_name:
            try:
                result = self.openai_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    n=1,
                    reasoning_effort=reasoning_effort,
                    verbosity=verbosity,
                    timeout=timeout,
                    stream=True,
                )
            except BaseException as e:
                print(f"OpenAIレスポンスエラー: {e}")
                raise (e)
        else:
            try:
                result = self.openai_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    n=1,
                    timeout=timeout,
                    stream=True,
                    temperature=temperature,
                )
            except BaseException as e:
                print(f"OpenAIレスポンスエラー: {e}")
                raise (e)
        yield from self.parse_output_stream_gpt_legacy(result, stream_per_sentence)

    def chat_anthropic(
        self,
        messages: list,
        model: str = "claude-3-7-sonnet-latest",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        timeout: Optional[float] = None,
        stream_per_sentence: bool = True,
    ) -> Generator[str, None, None]:
        """Claude3を使用してレスポンスを取得する

        Args:
            messages (list): 会話のメッセージ
            model (str): 使用するモデル名 (デフォルト: "claude-3-7-sonnet-latest")
            temperature (float): Claude3のtemperatureパラメータ (デフォルト: 0.7)
            max_tokens (int): 1回のリクエストで生成する最大トークン数 (デフォルト: 1024)
            timeout (float): リクエストのタイムアウト時間 (デフォルト: None)
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
            temperature=temperature,
            messages=user_messages,
            system=system_message,
            timeout=timeout,
        ) as result:
            yield from self.parse_output_stream_anthropic(result, stream_per_sentence)

    def chat_gemini(
        self,
        messages: list,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        timeout: Optional[float] = None,
        stream_per_sentence: bool = True,
    ) -> Generator[str, None, None]:
        """Geminiを使用してレスポンスを取得する

        Args:
            messages (list): 会話のメッセージ
            model (str): 使用するモデル名 (デフォルト: "gemini-2.0-flash")
            temperature (float): Geminiのtemperatureパラメータ (デフォルト: 0.7)
            max_tokens (int): 1回のリクエストで生成する最大トークン数 (デフォルト: 1024)
            timeout (float): リクエストのタイムアウト時間（秒） (デフォルト: None)
            stream_per_sentence (bool): 1文ごとにストリーミングするかどうか (デフォルト: True)
        Returns:
            Generator[str, None, None]): 会話の返答を順次生成する

        """
        if self.gemini_client is None:
            print("Gemini API key is not set.")
            return
        (
            system_instruction,
            history,
            cur_message,
        ) = self.convert_messages_from_gpt_to_gemini(copy.deepcopy(messages))
        timeout_ms = timeout * 1000 if timeout else None
        chat = self.gemini_client.chats.create(
            model=model,
            history=history,
            config=types.GenerateContentConfig(
                http_options=types.HttpOptions(
                    timeout=timeout_ms,
                ),
                system_instruction=system_instruction,
                temperature=temperature,
                max_output_tokens=max_tokens,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        try:
            responses = chat.send_message_stream(cur_message)
        except BaseException as e:
            print(f"Geminiレスポンスエラー: {e}")
        yield from self.parse_output_stream_gemini(responses, stream_per_sentence)

    def chat(
        self,
        messages: list,
        model: str = "gpt-4.1",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        reasoning_effort: str = "minimal",
        verbosity: str = "low",
        timeout: Optional[float] = None,
        stream_per_sentence: bool = True,
    ) -> Generator[str, None, None]:
        """指定したモデルを使用してレスポンスを取得する

        Args:
            messages (list): 会話のメッセージリスト
            model (str): 使用するモデル名 (デフォルト: "gpt-4.1")
            temperature (float): サンプリングの温度パラメータ (デフォルト: 0.7)
            max_tokens (int): 1回のリクエストで生成する最大トークン数 (デフォルト: 1024)
            reasoning_effort (str): 推論の努力レベル。gptでのみ使用可能。 ("minimal", "low", "medium", "high") (デフォルト: "minimal")
            verbosity (str): レスポンスの冗長性。gpt-5でのみ使用可能。 ("low", "medium", "high") (デフォルト: "low")
            timeout (float): リクエストのタイムアウト時間 (デフォルト: None)
            stream_per_sentence (bool): 1文ごとにストリーミングするかどうか (デフォルト: True)
        Returns:
            Generator[str, None, None]): 会話の返答を順次生成する

        """
        if (
            model in self.openai_model_name
            or model in self.openai_gpt5_model_name
            or model in self.openai_flagship_model_name
        ):
            yield from self.chat_gpt(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                reasoning_effort=reasoning_effort,
                verbosity=verbosity,
                timeout=timeout,
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
                max_tokens=max_tokens,
                timeout=timeout,
                stream_per_sentence=stream_per_sentence,
            )
        elif model in self.gemini_model_name:
            if self.gemini_client is None:
                print("Gemini API key is not set.")
                return
            try:
                yield from self.chat_gemini(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout,
                    stream_per_sentence=stream_per_sentence,
                )
            except BaseException as e:
                raise (e)
        else:
            print(f"Model name {model} can't use for this function")
            return

    def chat_anthropic_thinking(
        self,
        messages: list,
        model: str = "claude-3-7-sonnet-latest",
        max_tokens: int = 64000,
        budget_tokens: int = 10000,
        timeout: Optional[float] = None,
        stream_per_sentence: bool = True,
    ) -> Generator[str, None, None]:
        """Claudeを使用して拡張思考モードでレスポンスを取得する

        Args:
            messages (list): 会話のメッセージ
            model (str): 使用するモデル名 (デフォルト: ""claude-3-7-sonnet-latest")
            max_tokens (int): 1回のリクエストで生成する最大トークン数 (デフォルト: 64000)
            budget_tokens (int): 1回のリクエストで拡張思考に使用するトークン数 (デフォルト: 10000)
            timeout (float): リクエストのタイムアウト時間 (デフォルト: None)
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
            thinking={"type": "enabled", "budget_tokens": budget_tokens},
            timeout=timeout,
            messages=user_messages,
            system=system_message,
        ) as result:
            yield from self.parse_output_stream_anthropic(result, stream_per_sentence)

    def chat_gemini_thinking(
        self,
        messages: list,
        model: str = "gemini-2.5-flash-preview-04-17",
        temperature: float = 0.7,
        max_tokens: int = 64000,
        budget_tokens: int = 10000,
        timeout: Optional[float] = None,
        stream_per_sentence: bool = True,
    ) -> Generator[str, None, None]:
        """Gemini2.5 flashを使用して思考モードでレスポンスを取得する

        Args:
            messages (list): 会話のメッセージ
            model (str): 使用するモデル名 (デフォルト: "gemini-2.5-flash-preview-04-17")
            temperature (float): Geminiのtemperatureパラメータ (デフォルト: 0.7)
            max_tokens (int): 1回のリクエストで生成する最大トークン数 (デフォルト: 64000)
            budget_tokens (int): 1回のリクエストで思考に使用するトークン数 (デフォルト: 10000)
            timeout (float): リクエストのタイムアウト時間（秒） (デフォルト: None)
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
        timeout_ms = timeout * 1000 if timeout else None
        chat = self.gemini_client.chats.create(
            model=model,
            history=history,
            config=types.GenerateContentConfig(
                http_options=types.HttpOptions(
                    timeout=timeout_ms,
                ),
                system_instruction=system_instruction,
                max_output_tokens=max_tokens,
                temperature=temperature,
                thinking_config=types.ThinkingConfig(thinking_budget=budget_tokens),
            ),
        )
        responses = chat.send_message_stream(cur_message)
        yield from self.parse_output_stream_gemini(responses, stream_per_sentence)

    def chat_thinking(
        self,
        messages: list,
        model: str = "claude-3-7-sonnet-latest",
        temperature: float = 0.7,
        max_tokens: int = 64000,
        budget_tokens: int = 10000,
        reasoning_effort: str = "minimal",
        verbosity: str = "low",
        timeout: Optional[float] = None,
        stream_per_sentence: bool = True,
    ) -> Generator[str, None, None]:
        """指定したモデルを使用して、拡張思考を用いたレスポンスを取得する

        Args:
            messages (list): 会話のメッセージリスト
            model (str): 使用するモデル名 (デフォルト: "claude-3-7-sonnet-latest")
            temperature (float): サンプリングの温度パラメータ (デフォルト: 0.7)
            max_tokens (int): 1回のリクエストで生成する最大トークン数 (デフォルト: 64000)
            budget_tokens (int): 1回のリクエストで拡張思考に使用するトークン数。claude,geminiでのみ使用可能。 (デフォルト: 10000)
            reasoning_effort (str): 推論の努力レベル。gptでのみ使用可能。 ("minimal", "low", "medium", "high") (デフォルト: "minimal")
            verbosity (str): レスポンスの冗長性。gpt-5でのみ使用可能。 ("low", "medium", "high") (デフォルト: "low
            timeout (float): リクエストのタイムアウト時間 (デフォルト: None)
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
                budget_tokens=budget_tokens,
                timeout=timeout,
                stream_per_sentence=stream_per_sentence,
            )
        elif model in self.gemini_model_name:
            if GEMINI_APIKEY is None:
                print("Gemini API key is not set.")
                return
            yield from self.chat_gemini_thinking(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                budget_tokens=budget_tokens,
                timeout=timeout,
                stream_per_sentence=stream_per_sentence,
            )
        elif model in self.openai_flagship_model_name or model in self.openai_gpt5_model_name:
            if self.openai_client is None:
                raise ValueError("OpenAI API key is not set.")
            yield from self.chat_gpt(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                reasoning_effort=reasoning_effort,
                verbosity=verbosity,
                timeout=timeout,
                stream_per_sentence=stream_per_sentence,
            )
        else:
            print(f"Model name {model} can't use for this function")
            return

    def chat_gpt_web_search(
        self,
        messages: list,
        model: str = "gpt-4.1",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        timeout: Optional[float] = None,
        stream_per_sentence: bool = True,
    ) -> Generator[str, None, None]:
        """OpenAIモデルを使用してweb検索ありのレスポンスを取得する

        Args:
            messages (list): 会話のメッセージ
            model (str): 使用するモデル名 (デフォルト: "gpt-4.1")
            temperature (float): Geminiのtemperatureパラメータ (デフォルト: 0.7)
            timeout (float): リクエストのタイムアウト時間 (デフォルト: None)
            stream_per_sentence (bool): 1文ごとにストリーミングするかどうか (デフォルト: True)
        Returns:
            Generator[str, None, None]): 会話の返答を順次生成する

        """
        if self.openai_client is None:
            raise ValueError("OpenAI API key is not set.")
        result = None
        for message in messages:
            if message["role"] == "model":
                message["role"] = "assistant"
        try:
            result = self.openai_client.responses.create(
                model=model,
                input=messages,
                temperature=temperature,
                max_output_tokens=max_tokens,
                tools=[{"type": "web_search_preview"}],
                stream=True,
                timeout=timeout,
            )
        except BaseException as e:
            print(f"OpenAIレスポンスエラー: {e}")
            raise (e)
        yield from self.parse_output_stream_gpt(result, stream_per_sentence)

    def chat_anthropic_web_search(
        self,
        messages: list,
        model: str = "claude-3-7-sonnet-latest",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        timeout: Optional[float] = None,
        stream_per_sentence: bool = True,
    ) -> Generator[str, None, None]:
        """Claude3を使用してweb検索ありのレスポンスを取得する

        Args:
            messages (list): 会話のメッセージ
            model (str): 使用するモデル名 (デフォルト: "claude-3-7-sonnet-latest")
            temperature (float): Claude3のtemperatureパラメータ (デフォルト: 0.7)
            max_tokens (int): 1回のリクエストで生成する最大トークン数 (デフォルト: 1024)
            timeout (float): リクエストのタイムアウト時間 (デフォルト: None)
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
            temperature=temperature,
            messages=user_messages,
            system=system_message,
            timeout=timeout,
            tools=[
                {"type": "web_search_20250305", "name": "web_search", "max_uses": 5}
            ],
        ) as result:
            yield from self.parse_output_stream_anthropic(result, stream_per_sentence)

    def chat_gemini_web_search(
        self,
        messages: list,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        timeout: Optional[float] = None,
        stream_per_sentence: bool = True,
    ) -> Generator[str, None, None]:
        """Geminiを使用してweb検索ありのレスポンスを取得する

        Args:
            messages (list): 会話のメッセージ
            model (str): 使用するモデル名 (デフォルト: "gemini-2.0-flash")
            temperature (float): Geminiのtemperatureパラメータ (デフォルト: 0.7)
            max_tokens (int): 1回のリクエストで生成する最大トークン数 (デフォルト: 1024)
            timeout (float): リクエストのタイムアウト時間（秒） (デフォルト: None)
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
        timeout_ms = timeout * 1000 if timeout else None
        tools = [types.Tool(google_search=types.GoogleSearch())]
        chat = self.gemini_client.chats.create(
            model=model,
            history=history,
            config=types.GenerateContentConfig(
                http_options=types.HttpOptions(
                    timeout=timeout_ms,
                ),
                system_instruction=system_instruction,
                temperature=temperature,
                max_output_tokens=max_tokens,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                tools=tools,
            ),
        )
        responses = chat.send_message_stream(cur_message)
        yield from self.parse_output_stream_gemini(responses, stream_per_sentence)

    def chat_web_search(
        self,
        messages: list,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        timeout: Optional[float] = None,
        stream_per_sentence: bool = True,
    ) -> Generator[str, None, None]:
        """指定したモデルを使用して、拡張思考を用いたレスポンスを取得する

        Args:
            messages (list): 会話のメッセージリスト
            model (str): 使用するモデル名 (デフォルト: "gemini-2.0-flash")
            max_tokens (int): 1回のリクエストで生成する最大トークン数 (デフォルト: 1024)
            timeout (float): リクエストのタイムアウト時間 (デフォルト: None)
            stream_per_sentence (bool): 1文ごとにストリーミングするかどうか (デフォルト: True)
        Returns:
            Generator[str, None, None]): 会話の返答を順次生成する

        """
        if model in self.openai_model_name:
            if self.openai_client is None:
                print("OpenAI API key is not set.")
                return
            yield from self.chat_gpt_web_search(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
                stream_per_sentence=stream_per_sentence,
            )
        elif model in self.anthropic_model_name:
            if self.anthropic_client is None:
                print("Anthropic API key is not set.")
                return
            yield from self.chat_anthropic_web_search(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
                stream_per_sentence=stream_per_sentence,
            )
        elif model in self.gemini_model_name:
            if self.gemini_client is None:
                print("Gemini API key is not set.")
                return
            yield from self.chat_gemini_web_search(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
                stream_per_sentence=stream_per_sentence,
            )
        else:
            print(f"Model name {model} can't use for this function")
            return
