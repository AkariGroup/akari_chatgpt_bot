import argparse
import copy
import os
import sys
from concurrent import futures

import grpc
from lib.chat_akari_grpc import ChatStreamAkariGrpc

sys.path.append(os.path.join(os.path.dirname(__file__), "lib/grpc"))
import gpt_server_pb2
import gpt_server_pb2_grpc
import voice_server_pb2
import voice_server_pb2_grpc


class GptServer(gpt_server_pb2_grpc.GptServerServiceServicer):
    """
    chatGPTにtextを送信し、返答をvoice_serverに送るgRPCサーバ
    """

    def __init__(self) -> None:
        self.chat_stream_akari_grpc = ChatStreamAkariGrpc()
        self.SYSTEM_PROMPT_PATH = (
            f"{os.path.dirname(os.path.realpath(__file__))}/config/system_prompt.txt"
        )
        self.messages = []
        with open(self.SYSTEM_PROMPT_PATH, "r") as f:
            self.messages = [
                self.chat_stream_akari_grpc.create_message(f.read(), role="system")
            ]
        voice_channel = grpc.insecure_channel("localhost:10002")
        self.stub = voice_server_pb2_grpc.VoiceServerServiceStub(voice_channel)

    def SetGpt(
        self, request: gpt_server_pb2.SetGptRequest(), context: grpc.ServicerContext
    ) -> gpt_server_pb2.SetGptReply:
        response = ""
        is_finish = True
        if request.HasField("is_finish"):
            is_finish = request.is_finish
        if len(request.text) < 2:
            return gpt_server_pb2.SetGptReply(success=True)
        print(f"Receive: {request.text}")
        content = f"{request.text}。"
        tmp_messages = copy.deepcopy(self.messages)
        tmp_messages.append(self.chat_stream_akari_grpc.create_message(content))
        if is_finish:
            self.messages = copy.deepcopy(tmp_messages)
            # 最終応答。高速生成するために、モデルはgpt-4o
            self.stub.StartHeadControl(voice_server_pb2.StartHeadControlRequest())
            for sentence in self.chat_stream_akari_grpc.chat(
                tmp_messages, model="gpt-4o"
            ):
                print(f"Send to voice server: {sentence}")
                self.stub.SetText(voice_server_pb2.SetTextRequest(text=sentence))
                response += sentence
            # Sentenceの終了を通知
            self.stub.SentenceEnd(voice_server_pb2.SentenceEndRequest())
            self.messages.append(
                self.chat_stream_akari_grpc.create_message(response, role="assistant")
            )
        else:
            # 途中での第一声とモーション準備。function_callingの確実性のため、モデルはgpt-4-turbo
            for sentence in self.chat_stream_akari_grpc.chat_and_motion(
                tmp_messages, model="gpt-4-turbo", short_response=True
            ):
                print(f"Send to voice server: {sentence}")
                self.stub.SetText(voice_server_pb2.SetTextRequest(text=sentence))
                response += sentence
        print("")
        return gpt_server_pb2.SetGptReply(success=True)

    def SendMotion(
        self, request: gpt_server_pb2.SendMotionRequest(), context: grpc.ServicerContext
    ) -> gpt_server_pb2.SendMotionReply:
        success = self.chat_stream_akari_grpc.send_reserved_motion()
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
    server.wait_for_termination()


if __name__ == "__main__":
    main()
