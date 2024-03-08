import argparse

import openai
from lib.chat_akari import ChatStreamAkari
from lib.conf import OPENAI_APIKEY
from lib.voicevox import TextToVoiceVox


voicevox = False  # 音声合成を使う場合Trueに変更


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-m",
        "--model",
        nargs="+",
        type=str,
        default=["gpt-3.5-turbo-0613"],
        help="Model name list",
    )
    parser.add_argument("-s", "--system", default="", type=str, help="System prompt")
    args = parser.parse_args()

    if voicevox:
        text_to_voice = TextToVoiceVox(host, port)

    chat_stream_akri = ChatStreamAkari()
    # systemメッセージの作成
    messages_list = []
    for i in range(0, len(args.model)):
        messages_list.append(
            [chat_stream_akri.create_message(args.system, role="system")]
        )
    while True:
        print("文章をキーボード入力後、Enterを押してください。")
        text = input("Input: ")
        # userメッセージの追加
        print(f"User   : {text}")
        for i, model in enumerate(args.model):
            print(f"{model}: ")
            messages_list[i].append(chat_stream_akri.create_message(text))
            response = ""
            for sentence in chat_stream_akri.chat(messages_list[i], model=model):
                if voicevox:
                    text_to_voice.put_text(sentence)
                response += sentence
                print(sentence, end="", flush=True)
            # chatGPTの返答をassistantメッセージとして追加
            messages_list[i].append(
                chat_stream_akri.create_message(response, role="assistant")
            )
            print("")
            print("")


if __name__ == "__main__":
    main()
