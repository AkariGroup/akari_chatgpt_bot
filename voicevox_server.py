import argparse
import os
import sys
import time
from concurrent import futures

import grpc

sys.path.append(os.path.join(os.path.dirname(__file__), "lib/grpc"))
import voice_server_pb2
import voice_server_pb2_grpc


class VoiceServer(voice_server_pb2_grpc.VoiceServerServiceServicer):
    """
    Voicevoxにtextを送信し、音声を再生するgprcサーバ
    """

    def __init__(self, text_to_voice) -> None:
        self.text_to_voice = text_to_voice

    def SetText(
        self,
        request: voice_server_pb2.SetTextRequest(),
        context: grpc.ServicerContext,
    ) -> voice_server_pb2.SetTextReply:
        # 即時再生しないようにis_playはFalseで実行
        print(f"Send text: {request.text}")
        self.text_to_voice.put_text(request.text, play_now=False)
        return voice_server_pb2.SetTextReply(success=True)

    def SetStyleBertVitsParam(
        self,
        request: voice_server_pb2.SetStyleBertVitsParamRequest(),
        context: grpc.ServicerContext,
    ) -> voice_server_pb2.SetStyleBertVitsParamReply:
        print("SetStyleBertVitsParam is not supported on voicevox_server.")
        return voice_server_pb2.SetStyleBertVitsParamReply(success=False)

    def SetVoicevoxParam(
        self,
        request: voice_server_pb2.SetVoicevoxParamRequest(),
        context: grpc.ServicerContext,
    ) -> voice_server_pb2.SetVoicevoxParamReply:
        if request.speaker:
            self.text_to_voice.set_param(speaker=request.speaker)
        if request.speed_scale:
            self.text_to_voice.set_param(speed_scale=request.speed_scale)
        return voice_server_pb2.SetVoicevoxParamReply(success=True)

    def InterruptVoice(
        self,
        request: voice_server_pb2.InterruptVoiceRequest(),
        context: grpc.ServicerContext,
    ) -> voice_server_pb2.InterruptVoiceReply:
        while not self.text_to_voice.queue.empty():
            self.text_to_voice.queue.get()
        return voice_server_pb2.InterruptVoiceReply(success=True)

    def SetVoicePlayFlg(
        self,
        request: voice_server_pb2.SetVoicePlayFlgRequest(),
        context: grpc.ServicerContext,
    ) -> voice_server_pb2.SetVoicePlayFlgReply:
        self.text_to_voice.play_flg = request.flg
        return voice_server_pb2.SetVoicePlayFlgReply(success=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--voicevox_local", action="store_true")
    parser.add_argument(
        "--voice_host",
        type=str,
        default="127.0.0.1",
        help="VoiceVox server host",
    )
    parser.add_argument(
        "--voice_port",
        type=str,
        default="50021",
        help="VoiceVox server port",
    )
    args = parser.parse_args()
    if args.voicevox_local:
        # local版の場合
        from lib.voicevox import TextToVoiceVox

        voice_host = args.voice_host
        voice_port = args.voice_port
        text_to_voice = TextToVoiceVox(voice_host, voice_port)
        print("voicevox local pc ver.")
    else:
        # web版の場合
        from lib.conf import VOICEVOX_APIKEY
        from lib.voicevox import TextToVoiceVoxWeb

        text_to_voice = TextToVoiceVoxWeb(apikey=VOICEVOX_APIKEY)
        print("voicevox web ver.")

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    voice_server_pb2_grpc.add_VoiceServerServiceServicer_to_server(
        VoiceServer(text_to_voice), server
    )
    port = "10002"
    server.add_insecure_port("[::]:" + port)
    server.start()
    print(f"voice_server start. port: {port}")
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        exit()


if __name__ == "__main__":
    main()
