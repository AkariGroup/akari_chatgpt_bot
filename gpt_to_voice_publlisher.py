import argparse

import os
import sys
import openai
import grpc
from concurrent import futures
from lib.chat import chat_stream
from lib.conf import OPENAI_APIKEY
from lib.voicevox import TextToVoiceVox
import time
import copy

openai.api_key = OPENAI_APIKEY
host: str = ""
port: str = ""

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

    def SetGpt(self, request: gpt_server_pb2.SetGptRequest(), context):
        response = ""
        print(request.text)
        if len(request.text) < 2:
            return gpt_server_pb2.SetGptReply(success=True)
        if request.is_finish:
            content = f"{request.text}。普通に短文で簡潔に答えてください。"
        else:
            content = f"[{request.text}」という文に対して、以下の「」内からどれか一つを選択して回答してください。\n「えーと。」「はい、そうですね。」「そうですね…。」「いいえ、違います。」「こんにちは。」「ありがとうございます。」「よろしくおねがいします。」"
        tmp_messages = copy.deepcopy(self.messages)
        tmp_messages.append(
            # {'role': 'user', 'content': text + attention}
            {"role": "user", "content": content}
        )
        if request.is_finish:
            self.messages = copy.deepcopy(tmp_messages)
        print(self.messages)
        for sentence in chat_stream(tmp_messages):
            # if voicevox:
            #    text_to_voice.put_text(sentence)
            response += sentence
        print(sentence, end="")
        print("")
        if request.is_finish:
            self.messages.append({"role": "assistant", "content": response})
        return gpt_server_pb2.SetGptReply(success=True)


def main() -> None:
    global host
    global port
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--voicevox_host",
        type=str,
        default="127.0.0.1",
        help="VoiceVox server host",
    )
    parser.add_argument(
        "--voicevox_port",
        type=str,
        default="50021",
        help="VoiceVox server port",
    )
    args = parser.parse_args()
    host = args.voicevox_host
    port = args.voicevox_port
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
