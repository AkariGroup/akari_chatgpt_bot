import argparse

from lib.chat_akari import ChatStreamAkari
from lib.google_speech import MicrophoneStream, get_db_thresh, listen_print_loop

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
        "-m", "--model", help="LLM model name", default="gpt-3.5-turbo", type=str
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
    timeout: float = args.timeout
    power_threshold: float = args.power_threshold
    if power_threshold == 0:
        power_threshold = get_db_thresh() + POWER_THRESH_DIFF
    print(f"power_threshold set to {power_threshold:.3f}db")
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
        with MicrophoneStream(
            rate=RATE, chunk=CHUNK, _timeout_thresh=timeout, _db_thresh=power_threshold
        ) as stream:
            print("Enterを入力してください")
            input()
            responses = stream.transcribe()
            if responses is not None:
                text = listen_print_loop(responses)
        # chatGPT
        # 2文字以上の入力でない場合は回答しない。
        if len(text) >= 2:
            attention = "。120文字以内で回答してください。"
            messages.append({"role": "user", "content": text + attention})
            print(f"User   : {text}")
            print(f"{args.model} :")
            response = ""
            for sentence in chat_stream_akari.chat(messages, model=args.model):
                # 音声合成
                text_to_voice.put_text(sentence)
                response += sentence
                print(sentence, end="", flush=True)
            text_to_voice.sentence_end()
            messages.append({"role": "assistant", "content": response})
        print("")
        print("")


if __name__ == "__main__":
    main()
