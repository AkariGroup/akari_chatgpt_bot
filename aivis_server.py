import argparse
import os
import sys
import time
from concurrent import futures

import grpc
from lib.aivis import TextToAivis

sys.path.append(os.path.join(os.path.dirname(__file__), "lib/grpc"))
import voice_server_pb2
import voice_server_pb2_grpc


class VoiceServer(voice_server_pb2_grpc.VoiceServerServiceServicer):
    """
    Aivisにtextを送信し、音声を再生するgprcサーバ
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
        print("SetStyleBertVitsParam is not supported on aivis_server.")
        return voice_server_pb2.SetStyleBertVitsParamReply(success=True)

    def SetVoicevoxParam(
        self,
        request: voice_server_pb2.SetVoicevoxParamRequest(),
        context: grpc.ServicerContext,
    ) -> voice_server_pb2.SetVoicevoxParamReply:
        print("SetVoicevoxParam is not supported on aivis_server.")
        return voice_server_pb2.SetVoicevoxParamReply(success=False)

    def SetAivisParam(
        self,
        request: voice_server_pb2.SetAivisParamRequest(),
        context: grpc.ServicerContext,
    ) -> voice_server_pb2.SetAivisParamReply:
        self.text_to_voice.set_param(
            speaker=request.speaker,
            style=request.style,
            speed_scale=request.speed_scale,
        )
        return voice_server_pb2.SetAivisParamReply(success=True)

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

    def StartHeadControl(
        self,
        request: voice_server_pb2.StartHeadControlRequest(),
        context: grpc.ServicerContext,
    ) -> voice_server_pb2.StartHeadControlReply:
        self.text_to_voice.start_head_control()
        return voice_server_pb2.StartHeadControlReply(success=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--voice_host",
        type=str,
        default="127.0.0.1",
        help="Aivis-Speech server host",
    )
    parser.add_argument(
        "--voice_port",
        type=str,
        default="10101",
        help="Aivis-Speech server port",
    )
    parser.add_argument(
        "--robot_ip", help="Robot ip address", default="127.0.0.1", type=str
    )
    parser.add_argument(
        "--robot_port", help="Robot port number", default="50055", type=str
    )
    parser.add_argument(
        "--no_motion",
        help="Not play nod motion",
        action="store_true",
    )
    args = parser.parse_args()
    host = args.voice_host
    port = args.voice_port
    motion_server_host = None
    motion_server_port = None
    if not args.no_motion:
        motion_server_host = args.robot_ip
        motion_server_port = args.robot_port
    text_to_voice = TextToAivis(
        host=host,
        port=port,
        motion_host=motion_server_host,
        motion_port=motion_server_port,
    )

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    voice_server_pb2_grpc.add_VoiceServerServiceServicer_to_server(
        VoiceServer(text_to_voice), server
    )
    port = "10002"
    server.add_insecure_port("[::]:" + port)
    server.start()
    print(f"voice_server start. port: {port}")
    server.wait_for_termination()


if __name__ == "__main__":
    main()
