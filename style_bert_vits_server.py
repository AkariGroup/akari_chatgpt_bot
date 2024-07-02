import argparse
import os
import sys
import time
from concurrent import futures

import grpc
from lib.style_bert_vits import TextToStyleBertVits

sys.path.append(os.path.join(os.path.dirname(__file__), "lib/grpc"))
import voice_server_pb2
import voice_server_pb2_grpc


class VoiceServer(voice_server_pb2_grpc.VoiceServerServiceServicer):
    """
    StyleBertVitsにtextを送信し、音声を再生するgprcサーバ
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
        if request.model_name:
            self.text_to_voice.set_param(model_name=request.model_name)
        if request.length:
            self.text_to_voice.set_param(length=request.length)
        if request.style:
            self.text_to_voice.set_param(style=request.style)
        if request.style_weight:
            self.text_to_voice.set_param(style_weight=request.style_weight)
        return voice_server_pb2.SetStyleBertVitsParamReply(success=True)

    def SetVoicevoxParam(
        self,
        request: voice_server_pb2.SetVoicevoxParamRequest(),
        context: grpc.ServicerContext,
    ) -> voice_server_pb2.SetVoicevoxParamReply:
        print("SetVoicevoxParam is not supported on style_bert_vits_server.")
        return voice_server_pb2.SetVoicevoxParamReply(success=False)

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

    def IsVoicePlaying(
        self,
        request: voice_server_pb2.IsVoicePlayingRequest(),
        context: grpc.ServicerContext,
    ) -> voice_server_pb2.IsVoicePlayingReply:
        return voice_server_pb2.IsVoicePlayingReply(
            is_playing=not self.text_to_voice.is_playing()
        )

    def SentenceEnd(
        self,
        request: voice_server_pb2.SentenceEndRequest(),
        context: grpc.ServicerContext,
    ) -> voice_server_pb2.SentenceEndReply:
        self.text_to_voice.sentence_end()
        return voice_server_pb2.SentenceEndReply(success=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--voice_host",
        type=str,
        default="127.0.0.1",
        help="Style-Bert-VITS2 server host",
    )
    parser.add_argument(
        "--voice_port",
        type=str,
        default="5000",
        help="Style-Bert-VITS2 server port",
    )
    args = parser.parse_args()

    host = args.voice_host
    port = args.voice_port
    text_to_voice = TextToStyleBertVits(host, port)

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
