import argparse


def main() -> None:
    host = ""
    port = ""
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
        from lib.voicevox import TextToVoiceVox

        host = args.voice_host
        port = args.voice_port
        text_to_voice = TextToVoiceVox(host, port)
        print("voicevox local pc ver.")
    else:
        from lib.conf import VOICEVOX_APIKEY
        from lib.voicevox import TextToVoiceVoxWeb

        text_to_voice = TextToVoiceVoxWeb(apikey=VOICEVOX_APIKEY)
        print("voicevox web ver.")

    print("発話させたい文章をキーボード入力後、Enterを押してください。")
    while True:
        text = input("Input: ")
        text_to_voice.put_text(text)
        print("")


if __name__ == "__main__":
    main()
