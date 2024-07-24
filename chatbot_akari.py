import argparse
import os
import sys

import grpc
from lib.chat_akari import ChatStreamAkari

sys.path.append(os.path.join(os.path.dirname(__file__), "lib/grpc"))
import motion_server_pb2
import motion_server_pb2_grpc

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms
POWER_THRESH_DIFF = 25  # 周辺音量にこの値を足したものをpower_threshouldとする

host: str = ""
port: str = ""


def main() -> None:
    global host
    global port
    parser = argparse.ArgumentParser()
    parser.add_argument("--robot_ip", help="Ip address", default="127.0.0.1", type=str)
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
    parser.add_argument(
        "--v2",
        action="store_true",
        help="Use google speech v2 instead of v1",
    )
    parser.add_argument(
        "-m", "--model", help="LLM model name", default="gpt-4o", type=str
    )
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
    if args.v2:
        from lib.google_speech_v2 import MicrophoneStreamV2 as MicrophoneStream
        from lib.google_speech_v2 import get_db_thresh, listen_print_loop
    else:
        from lib.google_speech import MicrophoneStream, get_db_thresh, listen_print_loop
    timeout: float = args.timeout
    power_threshold: float = args.power_threshold
    if power_threshold == 0:
        power_threshold = get_db_thresh() + POWER_THRESH_DIFF
    print(f"power_threshold set to {power_threshold:.3f}db")
    if args.voicevox_local:
        from lib.voicevox import TextToVoiceVox

        host = args.voice_host
        port = args.voice_port
        text_to_voice = TextToVoiceVox(host, port)
    else:
        from lib.conf import VOICEVOX_APIKEY
        from lib.voicevox import TextToVoiceVoxWeb

        text_to_voice = TextToVoiceVoxWeb(apikey=VOICEVOX_APIKEY)

    channel = grpc.insecure_channel(args.robot_ip + ":" + str(args.robot_port))
    stub = motion_server_pb2_grpc.MotionServerServiceStub(channel)

    messages = [
        {
            "role": "system",
            "content": "チャットボットとしてロールプレイをします。あかりという名前の、カメラロボットとして振る舞ってください。句読点を多く使い返答してください。",
        }
    ]
    chat_stream_akari = ChatStreamAkari(args.robot_ip, args.robot_port)
    while True:
        # 音声認識
        text = ""
        responses = None
        with MicrophoneStream(
            rate=RATE, chunk=CHUNK, _timeout_thresh=timeout, _db_thresh=power_threshold
        ) as stream:
            print("Enterを入力してください")
            input()
            # うなずきモーション再生
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
                text = listen_print_loop(responses)
        # 2文字以上の入力でない場合は回答しない。
        if len(text) >= 2:
            # chatGPT
            attention = "。150文字以内で回答してください。"
            messages.append({"role": "user", "content": text + attention})
            print(f"User   : {text}")
            print(f"{args.model} :")
            response = ""
            # 音声合成
            for sentence in chat_stream_akari.chat_and_motion(
                messages, model=args.model
            ):
                text_to_voice.put_text(sentence)
                response += sentence
                print(sentence, end="", flush=True)
            text_to_voice.sentence_end()
            messages.append({"role": "assistant", "content": response})
            print("")
            print("")


if __name__ == "__main__":
    main()
