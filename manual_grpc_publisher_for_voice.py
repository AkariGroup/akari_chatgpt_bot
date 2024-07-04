import argparse
import os
import sys
import time
import grpc

sys.path.append(os.path.join(os.path.dirname(__file__), "lib/grpc"))
import voice_server_pb2
import voice_server_pb2_grpc


def main() -> None:
    global enable_input
    parser = argparse.ArgumentParser()
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
    voice_channel = grpc.insecure_channel(args.voice_ip + ":" + args.voice_port)
    voice_stub = voice_server_pb2_grpc.VoiceServerServiceStub(voice_channel)

    while True:
        print("文章をキーボード入力後、Enterを押してください。")
        text = input("Input: ")
        # userメッセージの追加
        print(f"User   : {text}")
        try:
            voice_stub.SetVoicePlayFlg(
                voice_server_pb2.SetVoicePlayFlgRequest(flg=True)
            )
            voice_stub.SetText(voice_server_pb2.SetTextRequest(text=text))
            voice_stub.SentenceEnd(voice_server_pb2.SentenceEndRequest())
        except BaseException:
            pass


if __name__ == "__main__":
    main()
