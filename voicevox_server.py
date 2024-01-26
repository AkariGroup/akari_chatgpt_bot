import argparse

import os
import sys
import grpc
import time
from concurrent import futures

sys.path.append(os.path.join(os.path.dirname(__file__), "lib/grpc"))
import voicevox_server_pb2
import voicevox_server_pb2_grpc


class VoicevoxServer(voicevox_server_pb2_grpc.VoicevoxServerServiceServicer):
    def __init__(self, text_to_voice):
        self.text_to_voice = text_to_voice

    def SetVoicevox(self, request: voicevox_server_pb2.SetVoicevoxRequest(), context):
        self.text_to_voice.put_text(request.text)

    def InterruptVoicevox(
        self, request: voicevox_server_pb2.SetVoicevoxRequest(), context
    ):
        while not self.text_to_voice.queue.empty():
            self.text_to_voice.queue.get()

    def SetVoicePlayFlg(
        self, request: voicevox_server_pb2.SetVoicevoxRequest(), context
    ):
        self.text_to_voice.play_flg = request.flg


def main() -> None:
    global host
    global port
    parser = argparse.ArgumentParser()
    parser.add_argument("--voicevox_local", action="store_true")
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
    if args.voicevox_local:
        from lib.voicevox import TextToVoiceVox

        host = args.voicevox_host
        port = args.voicevox_port
        text_to_voice = TextToVoiceVox(host, port)
    else:
        from lib.conf import VOICEVOX_APIKEY
        from lib.voicevox import TextToVoiceVoxWeb

        text_to_voice = TextToVoiceVoxWeb(apikey=VOICEVOX_APIKEY)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    voicevox_server_pb2_grpc.add_GptServerServiceServicer_to_server(
        VoicevoxServer(text_to_voice), server
    )
    port = "10002"
    server.add_insecure_port("[::]:" + port)
    server.start()
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        exit()


if __name__ == "__main__":
    main()
