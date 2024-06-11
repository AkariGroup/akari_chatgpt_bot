

import argparse
import copy
import os
import sys
from concurrent import futures

import grpc
from lib.chat_akari_grpc import ChatStreamAkariGrpc

sys.path.append(os.path.join(os.path.dirname(__file__), "lib/grpc"))
import voicevox_server_pb2_grpc
import voicevox_server_pb2
import style_bert_vits_server_pb2_grpc
import style_bert_vits_server_pb2
import gpt_server_pb2_grpc
import gpt_server_pb2

class GptServer(gpt_server_pb2_grpc.GptServerServiceServicer):
    """
    chatGPTにtextを送信し、返答をvoicevox_serverに送るgprcサーバ
    """

    def __init__(self, use_style_bert_vits: bool = False) -> None:
        self.chat_stream_akari_grpc = ChatStreamAkariGrpc()
        content = "チャットボットとしてロールプレイします。あかりという名前のカメラロボットとして振る舞ってください。性格はポジティブで元気です。"
        self.messages = [
            self.chat_stream_akari_grpc.create_message(content, role="system")
        ]
        self.use_style_bert_vits = use_style_bert_vits
        if self.use_style_bert_vits:
            voice_channel = grpc.insecure_channel("localhost:10002")
            self.stub = style_bert_vits_server_pb2_grpc.StyleBertVitsServerServiceStub(
                voice_channel)
        else:
            voice_channel = grpc.insecure_channel("localhost:10002")
            self.stub = voicevox_server_pb2_grpc.VoicevoxServerServiceStub(
                voice_channel)

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
        if is_finish:
            content = f"{request.text}。一文で簡潔に答えてください。"
        else:
            content = f"{request.text}。"
        tmp_messages = copy.deepcopy(self.messages)
        tmp_messages.append(
            self.chat_stream_akari_grpc.create_message(content))
        if is_finish:
            self.messages = copy.deepcopy(tmp_messages)
        if is_finish:
            # 最終応答。高速生成するために、モデルはgpt-3.5-turbo
            for sentence in self.chat_stream_akari_grpc.chat(
                tmp_messages, model="gpt-3.5-turbo"
            ):
                if self.use_style_bert_vits:
                    print(f"Send to style-bert-vits: {sentence}")
                    self.stub.SetText(
                        style_bert_vits_server_pb2.SetTextRequest(
                            text=sentence)
                    )
                else:
                    print(f"Send to voicevox: {sentence}")
                    self.stub.SetVoicevox(
                        voicevox_server_pb2.SetVoicevoxRequest(text=sentence)
                    )
                response += sentence
            self.messages.append(
                self.chat_stream_akari_grpc.create_message(
                    response, role="assistant")
            )
        else:
            # 途中での第一声とモーション準備。function_callingの確実性のため、モデルはgpt-4-turbo-preview
            for sentence in self.chat_stream_akari_grpc.chat_and_motion(
                tmp_messages, model="gpt-4o", short_response=True
            ):
                if self.use_style_bert_vits:
                    print(f"Send to style-bert-vits: {sentence}")
                    self.stub.SetText(
                        style_bert_vits_server_pb2.SetTextRequest(
                            text=sentence)
                    )
                else:
                    print(f"Send to voicevox: {sentence}")
                    self.stub.SetVoicevox(
                        voicevox_server_pb2.SetVoicevoxRequest(text=sentence)
                    )
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
    parser.add_argument(
        "--use_style_bert_vits", help="Use Style-Bert-VITS2 instead of voicevox", action="store_true"
    )
    args = parser.parse_args()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    gpt_server_pb2_grpc.add_GptServerServiceServicer_to_server(
        GptServer(use_style_bert_vits=args.use_style_bert_vits), server)
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
