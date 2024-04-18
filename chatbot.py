import argparse

from lib.chat_akari import ChatStreamAkari
from lib.google_speech import MicrophoneStream, listen_print_loop

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

host: str = ""
port: str = ""


def main() -> None:
    global host
    global port
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-m", "--model", help="LLM model name", default="gpt-3.5-turbo-0613", type=str
    )
    parser.add_argument("--voicevox_local", action="store_true")
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
    if args.voicevox_local:
        from lib.voicevox import TextToVoiceVox

        host = args.voicevox_host
        port = args.voicevox_port
        text_to_voice = TextToVoiceVox(host, port)
    else:
        from lib.conf import VOICEVOX_APIKEY
        from lib.voicevox import TextToVoiceVoxWeb

        text_to_voice = TextToVoiceVoxWeb(apikey=VOICEVOX_APIKEY)

    chat_stream_akari = ChatStreamAkari()
    messages = [{"role": "system", "content": "チャットボットとしてロールプレイをします。"}]
    while True:
        # 音声認識
        text = ""
        responses = None
        with MicrophoneStream(RATE, CHUNK) as stream:
            print("Enterを入力してください")
            input()
            responses = stream.transcribe()
            if responses is not None:
                text = listen_print_loop(responses)
        # chatGPT
        attention = "。120文字以内で回答してください。"
        messages.append({"role": "user", "content": text + attention})
        print(f"User   : {text}")
        print(f"{args.model} :")
        response = ""
        # 音声合成
        for sentence in chat_stream_akari.chat(messages, model=args.model):
            text_to_voice.put_text(sentence)
            response += sentence
            print(sentence, end="", flush=True)
        messages.append({"role": "assistant", "content": response})
        print("")
        print("")


if __name__ == "__main__":
    main()
