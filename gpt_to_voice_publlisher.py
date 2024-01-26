import argparse

import os
import sys
import openai
import grpc
from concurrent import futures
from lib.chat import chat_stream
from lib.conf import OPENAI_APIKEY
import time

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

    def SetGpt(self, request: gpt_server_pb2.SetGptRequest(), context):
        response = ""
        self.messages.append(
            # {'role': 'user', 'content': text + attention}
            {"role": "user", "content": request.text}
        )
        for sentence in chat_stream(self.messages):
            self.stub.SetVoicevox(voicevox_server_pb2.SetVoicevoxRequest(text=sentence))
            response += sentence
        print(sentence, end="")
        self.messages.append({"role": "assistant", "content": response})


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
            time.sleep(0.1)
    except KeyboardInterrupt:
        exit()


if __name__ == "__main__":
    main()
