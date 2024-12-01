import argparse
import os
import sys
import time

import grpc

sys.path.append(os.path.join(os.path.dirname(__file__), "lib/grpc"))
import gpt_server_pb2
import gpt_server_pb2_grpc
import voice_server_pb2
import voice_server_pb2_grpc


def main() -> None:
    global enable_input
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--gpt_ip", help="Gpt server ip address", default="127.0.0.1", type=str
    )
    parser.add_argument(
        "--gpt_port", help="Gpt server port number", default="10001", type=str
    )
    parser.add_argument(
        "--voice_ip", help="Voice server ip address", default="127.0.0.1", type=str
    )
    parser.add_argument(
        "--voice_port", help="Voice server port number", default="10002", type=str
    )
    parser.add_argument(
        "--no_motion",
        help="Not play nod motion",
        action="store_true",
    )
    args = parser.parse_args()
    # grpc stubの設定
    gpt_channel = grpc.insecure_channel(args.gpt_ip + ":" + args.gpt_port)
    gpt_stub = gpt_server_pb2_grpc.GptServerServiceStub(gpt_channel)
    voice_channel = grpc.insecure_channel(args.voice_ip + ":" + args.voice_port)
    voice_stub = voice_server_pb2_grpc.VoiceServerServiceStub(voice_channel)

    while True:
        print("文章をキーボード入力後、Enterを押してください。")
        text = input("Input: ")
        # userメッセージの追加
        print(f"User   : {text}")
        try:
            voice_stub.EnableVoicePlay(
                voice_server_pb2.EnableVoicePlayRequest()
            )
        except BaseException:
            pass
        try:
            gpt_stub.SetGpt(gpt_server_pb2.SetGptRequest(text=text, is_finish=True))
        except BaseException:
            print("SetGpt error")
            pass


if __name__ == "__main__":
    main()
