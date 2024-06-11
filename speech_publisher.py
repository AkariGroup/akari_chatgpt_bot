import argparse
import os
import sys

import grpc
from lib.google_speech import get_db_thresh
from lib.google_speech_grpc import GoogleSpeechGrpc, MicrophoneStreamGrpc

sys.path.append(os.path.join(os.path.dirname(__file__), "lib/grpc"))
import motion_server_pb2_grpc
import motion_server_pb2
import style_bert_vits_server_pb2_grpc
import style_bert_vits_server_pb2
import voicevox_server_pb2_grpc
import voicevox_server_pb2

RATE = 16000
CHUNK = int(RATE / 10)  # 100ms
POWER_THRESH_DIFF = 30  # 周辺音量にこの値を足したものをpower_threshouldとする


def main() -> None:
    global host
    global port
    parser = argparse.ArgumentParser()
    parser.add_argument("--robot_ip", help="Robot ip address",
                        default="127.0.0.1", type=str)
    parser.add_argument(
        "--robot_port", help="Robot port number", default="50055", type=str)
    parser.add_argument("--gpt_ip", help="Gpt server ip address",
                        default="127.0.0.1", type=str)
    parser.add_argument(
        "--gpt_port", help="Gpt server port number", default="10001", type=str)
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
        "--use_style_bert_vits", help="Use Style-Bert-VITS2 instead of voicevox", action="store_true"
    )
    args = parser.parse_args()
    timeout: float = args.timeout
    power_threshold: float = args.power_threshold

    # grpc stubの設定
    motion_channel = grpc.insecure_channel(
        args.robot_ip + ":" + str(args.robot_port))
    motion_stub = motion_server_pb2_grpc.MotionServerServiceStub(
        motion_channel)
    voice_channel = grpc.insecure_channel(
        args.voice_ip + ":" + args.voice_port
    )
    use_style_bert_vits = args.use_style_bert_vits
    if use_style_bert_vits:
        voice_stub = style_bert_vits_server_pb2_grpc.StyleBertVitsServerServiceStub(
            voice_channel
        )
    else:
        voice_stub = voicevox_server_pb2_grpc.VoicevoxServerServiceStub(
            voice_channel)

    google_speech_grpc = GoogleSpeechGrpc(
        gpt_host=args.gpt_ip,
        gpt_port=args.gpt_port,
        voice_host=args.voice_ip,
        voice_port=args.voice_port,
        use_style_bert_vits=args.use_style_bert_vits
    )
    # power_threshouldが指定されていない場合、周辺音量を収録し、発話判定閾値を決定
    if power_threshold == 0:
        power_threshold = get_db_thresh() + POWER_THRESH_DIFF
    print(f"power_threshold set to {power_threshold:.3f}db")

    while True:
        responses = None
        with MicrophoneStreamGrpc(RATE, CHUNK, timeout, power_threshold, use_style_bert_vits=args.use_style_bert_vits) as stream:
            print("Enterを入力してから、マイクに話しかけてください")
            input()
            if use_style_bert_vits:
                try:
                    voice_stub.SetVoicePlayFlg(
                        style_bert_vits_server_pb2.SetVoicePlayFlgRequest(
                            flg=False)
                    )
                except BaseException:
                    pass
            else:
                try:
                    voice_stub.SetVoicePlayFlg(
                        voicevox_server_pb2.SetVoicePlayFlgRequest(flg=False)
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
                    print("akari_motion_server is not working.")
            responses = stream.transcribe()
            if responses is not None:
                google_speech_grpc.listen_publisher_grpc(
                    responses, progress_report_len=args.progress_report_len
                )
        print("")


if __name__ == "__main__":
    main()
