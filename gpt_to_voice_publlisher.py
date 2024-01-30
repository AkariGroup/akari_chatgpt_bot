import argparse

import os
import sys
import openai
import grpc
from concurrent import futures
from lib.chat import chat_stream
from lib.chat_akari_server import ChatStreamAkariServer
from lib.conf import OPENAI_APIKEY
import time
import copy

openai.api_key = OPENAI_APIKEY

sys.path.append(os.path.join(os.path.dirname(__file__), "lib/grpc"))
import gpt_server_pb2
import gpt_server_pb2_grpc
import voicevox_server_pb2
import voicevox_server_pb2_grpc


class GptServer(gpt_server_pb2_grpc.GptServerServiceServicer):
    def __init__(self):
        self.messages = [
            {
                "role": "system",
                "content": "チャットボットとしてロールプレイします。あかりという名前のカメラロボットとして振る舞ってください。正確はポジティブで元気です。",
            },
        ]
        channel = grpc.insecure_channel("localhost:10002")
        self.stub = voicevox_server_pb2_grpc.VoicevoxServerServiceStub(channel)
        self.chat_stream_akari_server = ChatStreamAkariServer()

    def SetGpt(self, request: gpt_server_pb2.SetGptRequest(), context):
        response = ""
        if len(request.text) < 2:
            return gpt_server_pb2.SetGptReply(success=True)
        if request.is_finish:
            content = f"{request.text}。一文で簡潔に答えてください。"
        else:
            content = f"「{request.text}」という文に対して、以下の「」内からどれか一つを選択して、それだけ回答してください。\n「えーと。」「はい。」「う〜ん。」「いいえ。」「はい、そうですね。」「そうですね…。」「いいえ、違います。」「こんにちは。」「ありがとうございます。」「なるほど。」「まあ。」"
        tmp_messages = copy.deepcopy(self.messages)
        tmp_messages.append(
            # {'role': 'user', 'content': text + attention}
            {"role": "user", "content": content}
        )
        if request.is_finish:
            self.messages = copy.deepcopy(tmp_messages)
        if request.is_finish:
            for sentence in chat_stream(tmp_messages):
                print(sentence)
                self.stub.SetVoicevox(
                    voicevox_server_pb2.SetVoicevoxRequest(text=sentence)
                )
                self.messages.append({"role": "assistant", "content": response})
                response += sentence
                print(response)
        else:
            for sentence in self.chat_stream_akari_server.chat(tmp_messages):
                print(sentence)
                self.stub.SetVoicevox(
                    voicevox_server_pb2.SetVoicevoxRequest(text=sentence)
                )
                response += sentence
                print(response)
        print("")
        return gpt_server_pb2.SetGptReply(success=True)

    def SendMotion(self, request: gpt_server_pb2.SendMotionRequest(), context):
        success = self.chat_stream_akari_server.send_motion()
        return gpt_server_pb2.SendMotionReply(success=success)


def main() -> None:
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    gpt_server_pb2_grpc.add_GptServerServiceServicer_to_server(GptServer(), server)
    port = "10001"
    server.add_insecure_port("[::]:" + port)
    server.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        exit()


if __name__ == "__main__":
    main()
