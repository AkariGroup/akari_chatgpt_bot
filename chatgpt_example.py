import argparse
import os
import time

from lib.chat_akari import ChatStreamAkari
from lib.voicevox import TextToVoiceVox

voicevox = False  # 音声合成を使う場合Trueに変更


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-m",
        "--model",
        nargs="+",
        type=str,
        default=["gpt-4o"],
        help="Model name list",
    )
    parser.add_argument("-s", "--system", default="", type=str, help="System prompt")
    parser.add_argument(
        "--thinking",
        action="store_true",
        help="Use thinking mode (anthropic model only)",
    )
    parser.add_argument(
        "--web_search",
        action="store_true",
        help="Use web search grounding (gemini model only)",
    )
    args = parser.parse_args()
    chat_stream_akari = ChatStreamAkari()
    # systemメッセージの作成
    messages_list = []
    content = None
    if args.system == "":
        SYSTEM_PROMPT_PATH = (
            f"{os.path.dirname(os.path.realpath(__file__))}/config/system_prompt.txt"
        )
        content = open(SYSTEM_PROMPT_PATH, "r").read()
    else:
        content = args.system
    for i in range(0, len(args.model)):
        messages_list.append([chat_stream_akari.create_message(content, role="system")])
    while True:
        print("文章をキーボード入力後、Enterを押してください。")
        text = input("Input: ")
        # userメッセージの追加
        print(f"User   : {text}")
        for i, model in enumerate(args.model):
            print(f"{model}: ")
            messages_list[i].append(chat_stream_akari.create_message(text))
            response = ""
            start = time.time()
            if args.thinking:
                for sentence in chat_stream_akari.chat_thinking(
                    messages_list[i],
                    model=model,
                    stream_per_sentence=True,
                ):
                    response += sentence
                    print(sentence, end="", flush=True)
            elif args.web_search:
                for sentence in chat_stream_akari.chat_web_search(
                    messages_list[i],
                    model=model,
                    stream_per_sentence=True,
                ):
                    response += sentence
                    print(sentence, end="", flush=True)
            else:
                for sentence in chat_stream_akari.chat(
                    messages_list[i],
                    model=model,
                    stream_per_sentence=True,
                    temperature=0.7,
                ):
                    response += sentence
                    print(sentence, end="", flush=True)
            # chatGPTの返答をassistantメッセージとして追加
            messages_list[i].append(
                chat_stream_akari.create_message(response, role="assistant")
            )
            interval = time.time() - start
            print("")
            print("-------------------------")
            print(f"time: {interval:.2f} [s]")
            print("")


if __name__ == "__main__":
    main()
