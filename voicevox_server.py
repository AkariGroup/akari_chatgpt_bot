import argparse
import os
import sys
import time
from concurrent import futures

import grpc

sys.path.append(os.path.join(os.path.dirname(__file__), "lib/grpc"))
import voicevox_server_pb2
import voicevox_server_pb2_grpc


class VoicevoxServer(voicevox_server_pb2_grpc.VoicevoxServerServiceServicer):
    """
    Voicevoxにtextを送信し、音声を再生するgprcサーバ
    """

    def __init__(self, text_to_voice):
        self.text_to_voice = text_to_voice

    def SetVoicevox(
        self,
        request: voicevox_server_pb2.SetVoicevoxRequest(),
        context: grpc.ServicerContext,
    ) -> voicevox_server_pb2.SetVoicevoxReply:
        # 即時再生しないようにis_playはFalseで実行
        print(f"Send text: {request.text}")
        self.text_to_voice.put_text(request.text, play_now=False)
        return voicevox_server_pb2.SetVoicevoxReply(success=True)

    def InterruptVoicevox(
        self,
        request: voicevox_server_pb2.SetVoicevoxRequest(),
        context: grpc.ServicerContext,
    ) -> voicevox_server_pb2.InterruptVoicevoxReply:
        while not self.text_to_voice.queue.empty():
            self.text_to_voice.queue.get()
        return voicevox_server_pb2.InterruptVoicevoxReply(success=True)

    def SetVoicePlayFlg(
        self,
        request: voicevox_server_pb2.SetVoicevoxRequest(),
        context: grpc.ServicerContext,
    ) -> voicevox_server_pb2.SetVoicePlayFlgReply:
        self.text_to_voice.play_flg = request.flg
        return voicevox_server_pb2.SetVoicePlayFlgReply(success=True)


def main() -> None:
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
        # local版の場合
        from lib.voicevox import TextToVoiceVox

        voicevox_host = args.voicevox_host
        voicevox_port = args.voicevox_port
        text_to_voice = TextToVoiceVox(voicevox_host, voicevox_port)
        print(f"voicevox local pc ver.")
    else:
        # web版の場合
        from lib.conf import VOICEVOX_APIKEY
        from lib.voicevox import TextToVoiceVoxWeb

        text_to_voice = TextToVoiceVoxWeb(apikey=VOICEVOX_APIKEY)
        print(f"voicevox web ver.")

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    voicevox_server_pb2_grpc.add_VoicevoxServerServiceServicer_to_server(
        VoicevoxServer(text_to_voice), server
    )
    port = "10002"
    server.add_insecure_port("[::]:" + port)
    server.start()
    print(f"voicevox_server start. port: {port}")
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        exit()


if __name__ == "__main__":
    main()
