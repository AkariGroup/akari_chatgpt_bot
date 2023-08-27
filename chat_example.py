import argparse

import openai
from lib.chat import chat_stream
from lib.conf import OPENAI_APIKEY
from lib.voicevox import TextToVoiceVox

openai.api_key = OPENAI_APIKEY
host: str = ""
port: str = ""

voicevox = False  # 音声合成を使う場合Trueに変更


def main() -> None:
    global host
    global port
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--voicevox_host",
        type=str,
        default="127.0.0.1",
        help="VoiceVox server host",
    )
    parser.add_argument(
        "--voicevox_port",
        type=str,
        default="50021",
        help="VoiceVox server port",
    )
    args = parser.parse_args()
    host = args.voicevox_host
    port = args.voicevox_port

    if voicevox:
        text_to_voice = TextToVoiceVox(host, port)
    messages = [
        {
            "role": "system",
            "content": "チャットボットとしてロールプレイします。あかりという名前のカメラロボットとして振る舞ってください。正確はポジティブで元気です。",
        },
    ]
    exit_flag = False
    while not exit_flag:
        text = input("Input: ")
        messages.append(
            # {'role': 'user', 'content': text + attention}
            {"role": "user", "content": text}
        )
        print(f"User   : {text}")
        print("ChatGPT: ")
        response = ""
        for sentence in chat_stream(messages):
            if voicevox:
                text_to_voice.put_text(sentence)
            response += sentence
            print(sentence, end="")
        messages.append({"role": "assistant", "content": response})
        print("")
        print("")


if __name__ == "__main__":
    main()
