import argparse


RATE = 16000
CHUNK = int(RATE / 10)  # 100ms
POWER_THRESH_DIFF = 25  # 周辺音量にこの値を足したものをpower_threshouldとする


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
        "--v2",
        action="store_true",
        help="Use google speech v2 instead of v1",
    )
    args = parser.parse_args()
    if args.v2:
        from lib.google_speech_v2 import MicrophoneStreamV2 as MicrophoneStream
        from lib.google_speech_v2 import get_db_thresh, listen_print_loop
    else:
        from lib.google_speech import MicrophoneStream, get_db_thresh, listen_print_loop
    timeout: float = args.timeout
    power_threshold: float = args.power_threshold
    if power_threshold == 0:
        power_threshold = get_db_thresh() + POWER_THRESH_DIFF
    print(f"power_threshold set to {power_threshold:.3f}db")

    print("マイクに話しかけてください")
    while True:
        responses = None
        with MicrophoneStream(
            rate=RATE, chunk=CHUNK, _timeout_thresh=timeout, _db_thresh=power_threshold
        ) as stream:
            responses = stream.transcribe()
            if responses is not None:
                listen_print_loop(responses)


if __name__ == "__main__":
    main()
