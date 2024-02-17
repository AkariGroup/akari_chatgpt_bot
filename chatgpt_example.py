import argparse

import openai
from lib.chat import chat_stream, create_message
from lib.conf import OPENAI_APIKEY
from lib.voicevox import TextToVoiceVox


voicevox = False  # 音声合成を使う場合Trueに変更


def main() -> None:
    parser = argparse.ArgumentParser()

    args = parser.parse_args()

    if voicevox:
        text_to_voice = TextToVoiceVox(host, port)
    # systemメッセージの作成
    content = "チャットボットとしてロールプレイします。あかりという名前のカメラロボットとして振る舞ってください。性格はポジティブで元気です。"
    messages = [create_message(content, role="system")]
    print("文章をキーボード入力後、Enterを押してください。")
    while True:
        text = input("Input: ")
        # userメッセージの追加
        messages.append(create_message(text))
        print(f"User   : {text}")
        print("ChatGPT: ")
        response = ""
        for sentence in chat_stream(messages):
            if voicevox:
                text_to_voice.put_text(sentence)
            response += sentence
            print(sentence, end="")
        # chatGPTの返答をassistantメッセージとして追加
        messages.append(create_message(response, role="assistant"))
        print("")
        print("")


if __name__ == "__main__":
    main()
