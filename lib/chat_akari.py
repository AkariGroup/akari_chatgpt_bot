import json
import os
import sys
import threading
import numpy as np
from typing import Generator

import anthropic
import grpc
import openai
from gpt_stream_parser import force_parse_json
from .conf import ANTHROPIC_APIKEY

sys.path.append(os.path.join(os.path.dirname(__file__), "grpc"))
import motion_server_pb2
import motion_server_pb2_grpc


class ChatStreamAkari(object):
    def __init__(
        self, motion_host: str = "localhost", motion_port: str = "50055"
    ) -> None:
        motion_channel = grpc.insecure_channel(motion_host + ":" + motion_port)
        self.motion_stub = motion_server_pb2_grpc.MotionServerServiceStub(motion_channel)
        self.anthropic_client = anthropic.Anthropic(
            api_key=ANTHROPIC_APIKEY,
        )
        self.last_char = ["、", "。", "！", "!", "?", "？", "\n"]
        self.openai_model_name = [
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
            "gpt-3.5-turbo-16k",
            "gpt-3.5-turbo-0613",
            "gpt-3.5-turbo-16k-0613",
        ]
        self.openai_vision_model_name = [
            "gpt-4-vision-preview",
            "gpt-4-1106-vision-preview",
        ]
        self.anthropic_model_name = [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2",
        ]

    def create_message(self, text: str, role: str = "user") -> str:
        message = {"role": role, "content": text}
        return message

    def cv_to_base64(self, image: np.ndarray) -> str:
        _, encoded = cv2.imencode(".jpg", image)
        return base64.b64encode(encoded).decode("ascii")

    def create_vision_message(self, text: str, image: np.ndarray) -> str:
        resized_image = cv2.resize(image, (480, 270))
        base64_image = cv_to_base64(resized_image)
        url = f"data:image/jpeg;base64,{base64_image}"
        message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": text,
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": url,
                    },
                },
            ],
        }
        return message

    def send_motion(self, name: str) -> None:
        try:
            self.motion_stub.SetMotion(
                motion_server_pb2.SetMotionRequest(
                    name=name, priority=3, repeat=False, clear=True
                )
            )
        except BaseException:
            print("send error!")
            pass

    """
    def chat_anthropic(
        self,
        messages: list,
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
    """

    def chat_gpt(
        self,
        messages: list,
        model: str = "gpt-3.5-turbo-0613",
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        result = None
        if model in self.openai_vision_model_name:
            result = openai.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=1024,
                n=1,
                stream=True,
                temperature=temperature,
            )
        elif model in self.openai_model_name:
            result = openai.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=1024,
                n=1,
                stream=True,
                temperature=temperature,
                stop=None,
            )
        fullResponse = ""
        RealTimeResponce = ""
        for chunk in result:
            text = chunk.choices[0].delta.content
            if text is None:
                pass
            else:
                fullResponse += text
                RealTimeResponce += text

                for index, char in enumerate(RealTimeResponce):
                    if char in self.last_char:
                        pos = index + 1  # 区切り位置
                        sentence = RealTimeResponce[:pos]  # 1文の区切り
                        RealTimeResponce = RealTimeResponce[pos:]  # 残りの部分
                        # 1文完成ごとにテキストを読み上げる(遅延時間短縮のため)
                        yield sentence
                        break
                    else:
                        pass

    def chat(
        self,
        messages: list,
        model: str = "gpt-3.5-turbo-0613",
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        if model in self.openai_model_name or model in self.openai_vision_model_name:
            yield from self.chat_gpt(
                messages=messages, model=model, temperature=temperature
            )
        else:
            print(f"Model name {model} can't use for this function")
            return

    def chat_and_motion_gpt(
        self,
        messages: list,
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
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
        fullResponse = ""
        RealTimeResponse = ""
        sentence_index = 0
        get_motion = False
        for chunk in result:
            delta = chunk.choices[0].delta
            if delta.function_call is not None:
                if delta.function_call.arguments is not None:
                    fullResponse += chunk.choices[0].delta.function_call.arguments
                    try:
                        data_json = json.loads(fullResponse)
                        found_last_char = False
                        for char in self.last_char:
                            if RealTimeResponse[-1].find(char) >= 0:
                                found_last_char = True
                        if not found_last_char:
                            data_json["talk"] = data_json["talk"] + "。"
                    except BaseException:
                        data_json = force_parse_json(fullResponse)
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
                            RealTimeResponse = str(data_json["talk"])
                            for char in self.last_char:
                                pos = RealTimeResponse[sentence_index:].find(char)
                                if pos >= 0:
                                    sentence = RealTimeResponse[
                                        sentence_index : sentence_index + pos + 1
                                    ]
                                    sentence_index += pos + 1
                                    yield sentence
                                    break

    def chat_and_motion(
        self,
        messages: list,
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        if model in self.openai_model_name:
            yield from self.chat_and_motion_gpt(
                messages=messages, model=model, temperature=temperature
            )
        else:
            print(f"Model name {model} can't use for this function")
            return
