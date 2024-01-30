import json
import os
import sys
import threading
from typing import Generator

import grpc
import openai
from gpt_stream_parser import force_parse_json

sys.path.append(os.path.join(os.path.dirname(__file__), "grpc"))
import motion_server_pb2
import motion_server_pb2_grpc

last_char = ["、", "。", ".", "！", "？", "\n"]


class ChatStreamAkari:
    def __init__(self, host: str="localhost", port: str="50055") -> None:
        channel = grpc.insecure_channel(host + ":" + port)
        self.stub = motion_server_pb2_grpc.MotionServerServiceStub(channel)

    def send_motion(self, name: str) -> None:
        try:
            self.stub.SetMotion(
                motion_server_pb2.SetMotionRequest(
                    name=name, priority=3, repeat=False, clear=True
                )
            )
        except BaseException:
            print("send error!")
            pass

    def chat(self, messages: list) -> Generator[str, None, None]:
        result = openai.ChatCompletion.create(
            model="gpt-4-turbo-preview",
            messages=messages,
            n=1,
            temperature=0.7,
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
            if "function_call" in delta:
                if "arguments" in delta.function_call:
                    fullResponse += chunk.choices[0].delta.function_call.arguments
                    try:
                        data_json = json.loads(fullResponse)
                        found_last_char = False
                        for char in last_char:
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
                            for char in last_char:
                                pos = RealTimeResponse[sentence_index:].find(char)
                                if pos >= 0:
                                    sentence = RealTimeResponse[
                                        sentence_index : sentence_index + pos + 1
                                    ]
                                    sentence_index += pos + 1
                                    yield sentence
                                    break
