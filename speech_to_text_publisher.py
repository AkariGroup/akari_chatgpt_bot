import argparse
import os
import sys
import grpc

from lib.transcribe_google_speech import (
    MicrophoneStream,
    get_db_thresh,
    listen_print_loop,
    listen_publisher
)
sys.path.append(os.path.join(os.path.dirname(__file__), "lib/grpc"))
import motion_server_pb2
import motion_server_pb2_grpc
import voicevox_server_pb2
import voicevox_server_pb2_grpc

RATE = 16000
CHUNK = int(RATE / 10)  # 100ms
POWER_THRESH_DIFF = 30  # 周辺音量にこの値を足したものをpower_threshouldとする


def main() -> None:
    global host
    global port
    parser = argparse.ArgumentParser()
    parser.add_argument("--robot_ip", help="Ip address", default="0.0.0.0", type=str)
    parser.add_argument("--robot_port", help="Port number", default="50055", type=str)
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
    args = parser.parse_args()
    timeout: float = args.timeout
    power_threshold: float = args.power_threshold
    channel = grpc.insecure_channel(args.robot_ip + ":" + str(args.robot_port))
    stub = motion_server_pb2_grpc.MotionServerServiceStub(channel)
    voicevox_channel = grpc.insecure_channel("localhost:10002")
    voicevox_stub = voicevox_server_pb2_grpc.VoicevoxServerServiceStub(voicevox_channel)
    if power_threshold == 0:
        power_threshold = get_db_thresh() + POWER_THRESH_DIFF
    print(f"power_threshold set to {power_threshold:.3f}db")

    print("マイクに話しかけてください")
    while True:
        responses = None
        with MicrophoneStream(RATE, CHUNK, timeout, power_threshold) as stream:
            print("Enterを入力してください")
            input()
            try:
                voicevox_stub.SetVoicePlayFlg(
                    voicevox_server_pb2.SetVoicePlayFlgRequest(flg=False)
                )
            except BaseException:
                pass
            try:
                stub.SetMotion(
                    motion_server_pb2.SetMotionRequest(
                        name="nod", priority=3, repeat=True
                    )
                )
            except BaseException:
                print("akari_motion_server is not working.")
            responses = stream.transcribe()
            if responses is not None:
                listen_publisher(responses)
        print("")


if __name__ == "__main__":
    main()
