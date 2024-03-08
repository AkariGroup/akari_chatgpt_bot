import json
import os
import sys
from typing import Generator

import grpc
import openai
from gpt_stream_parser import force_parse_json

from .chat_akari import ChatStreamAkari

sys.path.append(os.path.join(os.path.dirname(__file__), "grpc"))
import motion_server_pb2
import motion_server_pb2_grpc


class ChatStreamAkariGrpc(ChatStreamAkari):
    def __init__(
        self, motion_host: str = "127.0.0.1", motion_port: str = "50055"
    ) -> None:
        super().__init__(motion_host, motion_port)
        self.cur_motion_name = ""

    def send_motion(self) -> bool:
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
                        for char in last_char:
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
