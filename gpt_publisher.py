import argparse

import os
import sys
import openai
import grpc
from concurrent import futures
from lib.chat_akari_grpc import ChatStreamAkariGrpc
from lib.conf import OPENAI_APIKEY
import copy

sys.path.append(os.path.join(os.path.dirname(__file__), "lib/grpc"))
import gpt_server_pb2
import gpt_server_pb2_grpc
import voicevox_server_pb2
import voicevox_server_pb2_grpc


class GptServer(gpt_server_pb2_grpc.GptServerServiceServicer):
    """
    chatGPTにtextを送信し、返答をvoicevox_serverに送るgprcサーバ
    """

    def __init__(self):
        self.chat_stream_akari_grpc = ChatStreamAkariGrpc()
        content = "チャットボットとしてロールプレイします。あかりという名前のカメラロボットとして振る舞ってください。性格はポジティブで元気です。"
        self.messages = [
            self.chat_stream_akari_grpc.create_message(content, role="system")
        ]
        voicevox_channel = grpc.insecure_channel("localhost:10002")
        self.stub = voicevox_server_pb2_grpc.VoicevoxServerServiceStub(voicevox_channel)

    def SetGpt(
        self, request: gpt_server_pb2.SetGptRequest(), context: grpc.ServicerContext
    ) -> gpt_server_pb2.SetGptReply:
        response = ""
        if len(request.text) < 2:
            return gpt_server_pb2.SetGptReply(success=True)
        print(f"Receive: {request.text}")
        if request.is_finish:
            content = f"{request.text}。一文で簡潔に答えてください。"
        else:
            content = f"「{request.text}」という文に対して、以下の「」内からどれか一つを選択して、それだけ回答してください。\n「えーと。」「はい。」「うーん。」「いいえ。」「はい、そうですね。」「そうですね…。」「いいえ、違います。」「こんにちは。」「ありがとうございます。」「なるほど。」「まあ。」"
        tmp_messages = copy.deepcopy(self.messages)
        tmp_messages.append(self.chat_stream_akari_grpc.create_message(content))
        if request.is_finish:
            self.messages = copy.deepcopy(tmp_messages)
        if request.is_finish:
            for sentence in self.chat_stream_akari_grpc.chat(tmp_messages):
                print(f"Send voicevox: {sentence}")
                self.stub.SetVoicevox(
                    voicevox_server_pb2.SetVoicevoxRequest(text=sentence)
                )
                response += sentence
            self.messages.append(
                self.chat_stream_akari_grpc.create_message(
                    response, role="assistant"
                )
            )
        else:
            for sentence in self.chat_stream_akari_grpc.chat_and_motion(tmp_messages):
                print(f"Send voicevox: {sentence}")
                self.stub.SetVoicevox(
                    voicevox_server_pb2.SetVoicevoxRequest(text=sentence)
                )
                response += sentence
        print("")
        return gpt_server_pb2.SetGptReply(success=True)

    def SendMotion(
        self, request: gpt_server_pb2.SendMotionRequest(), context: grpc.ServicerContext
    ) -> gpt_server_pb2.SendMotionReply:
        success = self.chat_stream_akari_grpc.send_motion()
        return gpt_server_pb2.SendMotionReply(success=success)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ip", help="Gpt server ip address", default="127.0.0.1", type=str
    )
    parser.add_argument(
        "--port", help="Gpt server port number", default="10001", type=str
    )
    args = parser.parse_args()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    gpt_server_pb2_grpc.add_GptServerServiceServicer_to_server(GptServer(), server)
    server.add_insecure_port(args.ip + ":" + args.port)
    server.start()
    print(f"gpt_publisher start. port: {args.port}")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        exit()


if __name__ == "__main__":
    main()
