import argparse

import openai
from lib.chat import chat_stream
from lib.conf import OPENAI_APIKEY
from lib.voicevox import TextToVoiceVox


voicevox = False  # 音声合成を使う場合Trueに変更


def main() -> None:
    parser = argparse.ArgumentParser()

    args = parser.parse_args()

    if voicevox:
        text_to_voice = TextToVoiceVox(host, port)
    messages = [
        {
            "role": "system",
            "content": "チャットボットとしてロールプレイします。あかりという名前のカメラロボットとして振る舞ってください。正確はポジティブで元気です。",
        },
    ]
    print("文章をキーボード入力後、Enterを押してください。")
    while True:
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
