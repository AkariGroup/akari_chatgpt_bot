import argparse

from lib.google_speech import MicrophoneStream, listen_print_loop

RATE = 16000
CHUNK = int(RATE / 10)  # 100ms


def main() -> None:
    global host
    global port

    print("マイクに話しかけてください")
    while True:
        responses = None
        with MicrophoneStream(RATE, CHUNK) as stream:
            responses = stream.transcribe()
            if responses is not None:
                listen_print_loop(responses)
        print("")


if __name__ == "__main__":
    main()
