import argparse
import os
import sys
import time
from concurrent import futures

import grpc
from lib.google_speech import get_db_thresh

sys.path.append(os.path.join(os.path.dirname(__file__), "lib/grpc"))
import motion_server_pb2
import motion_server_pb2_grpc
import speech_server_pb2
import speech_server_pb2_grpc
import voice_server_pb2
import voice_server_pb2_grpc

RATE = 16000
CHUNK = int(RATE / 10)  # 100ms
POWER_THRESH_DIFF = 30  # 周辺音量にこの値を足したものをpower_threshouldとする
enable_input = True


class SpeechServer(speech_server_pb2_grpc.SpeechServerServiceServicer):
    """
    音声入力の制御用のgRPCサーバ
    """

    def ToggleSpeech(
        self,
        request: speech_server_pb2.ToggleSpeechRequest,
        context: grpc.ServicerContext,
    ) -> speech_server_pb2.ToggleSpeechReply:
        global enable_input
        enable_input = request.enable
        return speech_server_pb2.ToggleSpeechReply(success=True)


def main() -> None:
    global enable_input
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--robot_ip", help="Robot ip address", default="127.0.0.1", type=str
    )
    parser.add_argument(
        "--robot_port", help="Robot port number", default="50055", type=str
    )
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
        "-t",
        "--timeout",
        type=float,
        default=0.5,
        help="Microphone input power timeout",
    )
    parser.add_argument(
        "-p",
        "--power_threshold",
        type=float,
        default=0,
        help="Microphone input power threshold",
    )
    parser.add_argument(
        "--progress_report_len",
        type=int,
        default=8,
        help="Send the progress of speech recognition if recognition word count over this number ",
    )
    parser.add_argument(
        "--no_motion",
        help="Not play nod motion",
        action="store_true",
    )
    parser.add_argument(
        "--auto",
        help="Skip keyboard input for speech recognition",
        action="store_true",
    )
    parser.add_argument(
        "--v2",
        action="store_true",
        help="Use google speech v2 instead of v1",
    )
    args = parser.parse_args()
    if args.v2:
        from lib.google_speech_v2_grpc import GoogleSpeechV2Grpc as GoogleSpeechGrpc
        from lib.google_speech_v2_grpc import (
            MicrophoneStreamV2Grpc as MicrophoneStreamGrpc,
        )
    else:
        from lib.google_speech_grpc import GoogleSpeechGrpc as GoogleSpeechGrpc
        from lib.google_speech_grpc import MicrophoneStreamGrpc as MicrophoneStreamGrpc
    timeout: float = args.timeout
    power_threshold: float = args.power_threshold

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    speech_server_pb2_grpc.add_SpeechServerServiceServicer_to_server(
        SpeechServer(), server
    )
    port = "10003"
    server.add_insecure_port("[::]:" + port)
    server.start()
    print(f"speech_server start. port: {port}")

    # grpc stubの設定
    motion_channel = grpc.insecure_channel(args.robot_ip + ":" + str(args.robot_port))
    motion_stub = motion_server_pb2_grpc.MotionServerServiceStub(motion_channel)
    voice_channel = grpc.insecure_channel(args.voice_ip + ":" + args.voice_port)
    voice_stub = voice_server_pb2_grpc.VoiceServerServiceStub(voice_channel)

    google_speech_grpc = GoogleSpeechGrpc(
        gpt_host=args.gpt_ip,
        gpt_port=args.gpt_port,
        voice_host=args.voice_ip,
        voice_port=args.voice_port,
    )
    # power_threshouldが指定されていない場合、周辺音量を収録し、発話判定閾値を決定
    if power_threshold == 0:
        power_threshold = get_db_thresh() + POWER_THRESH_DIFF
    print(f"power_threshold set to {power_threshold:.3f}db")

    while True:
        responses = None
        if enable_input:
            with MicrophoneStreamGrpc(
                rate=RATE,
                chunk=CHUNK,
                _timeout_thresh=timeout,
                _db_thresh=power_threshold,
                gpt_host=args.gpt_ip,
                gpt_port=args.gpt_port,
                voice_host=args.voice_ip,
                voice_port=args.voice_port,
            ) as stream:
                if not args.auto:
                    print("Enterを入力してから、マイクに話しかけてください")
                    input()
                    try:
                        voice_stub.SetVoicePlayFlg(
                            voice_server_pb2.SetVoicePlayFlgRequest(flg=False)
                        )
                    except BaseException:
                        pass
                if not args.no_motion:
                    try:
                        motion_stub.SetMotion(
                            motion_server_pb2.SetMotionRequest(
                                name="nod", priority=3, repeat=True
                            )
                        )
                    except BaseException:
                        pass
                responses = stream.transcribe()
                if not enable_input:
                    continue
                if responses is not None:
                    google_speech_grpc.listen_publisher_grpc(
                        responses, progress_report_len=args.progress_report_len
                    )
            print("")
        else:
            time.sleep(0.05)


if __name__ == "__main__":
    main()
