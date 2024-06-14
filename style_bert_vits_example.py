import argparse

from lib.style_bert_vits import TextToStyleBertVits


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
        default="5000",
        help="Voice server port",
    )
    args = parser.parse_args()
    host = args.voice_host
    port = args.voice_port
    text_to_voice = TextToStyleBertVits(host, port)

    # set_paramメソッドでモデル名や音声再生速度、感情スタイルなどを指定することができます。
    # モデル名を指定
    # text_to_voice.set_param(model_name='jvnv-F1-jp')
    # 音声再生速度を指定
    # text_to_voice.set_param(length=2.0)
    # 感情スタイルを指定
    # text_to_voice.set_param(style='Happy')
    # 感情スタイルの重みを指定
    # text_to_voice.set_param(style_weight=3.0)

    print("発話させたい文章をキーボード入力後、Enterを押してください。")
    while True:
        text = input("Input: ")
        text_to_voice.put_text(
            text=text,
        )
        print("")


if __name__ == "__main__":
    main()
