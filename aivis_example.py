import argparse

from lib.aivis import TextToAivis


def main() -> None:
    host = ""
    port = ""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--voice_host",
        type=str,
        default="127.0.0.1",
        help="Voice server host",
    )
    parser.add_argument(
        "--voice_port",
        type=str,
        default="10101",
        help="Voice server port",
    )
    args = parser.parse_args()
    host = args.voice_host
    port = args.voice_port
    text_to_voice = TextToAivis(host, port)

    print(f"Speaker一覧: {text_to_voice.get_speaker_names()}")

    # set_paramメソッドでモデル名や音声再生速度、感情スタイルなどを指定することができます。
    # モデル名を指定
    # text_to_voice.set_param(speaker='Anneli')
    # 音声再生速度を指定
    # text_to_voice.set_param(speed_scale=1.3)
    # 感情スタイルを指定
    # text_to_voice.set_param(style="怒り・悲しみ")

    print(f"現在のSpeaker: {text_to_voice.speaker}")
    print("")
    print(
        f"{text_to_voice.speaker}のスタイル一覧: {text_to_voice.get_style_names(text_to_voice.speaker)}"
    )
    print(f"現在のStyle: {text_to_voice.style}")
    print("")

    print("発話させたい文章をキーボード入力後、Enterを押してください。")
    while True:
        text = input("Input: ")
        text_to_voice.put_text(text=text, blocking=True)
        print("")


if __name__ == "__main__":
    main()
