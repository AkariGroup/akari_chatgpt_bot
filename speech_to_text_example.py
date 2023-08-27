import argparse

from lib.transcribe_google_speech import (
    MicrophoneStream,
    get_db_thresh,
    listen_print_loop,
)

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
    args = parser.parse_args()
    timeout: float = args.timeout
    power_threshold: float = args.power_threshold
    if power_threshold == 0:
        power_threshold = get_db_thresh() + POWER_THRESH_DIFF
    print(f"power_threshold set to {power_threshold:.3f}db")

    print("マイクに話しかけてください")
    while True:
        responses = None
        with MicrophoneStream(RATE, CHUNK, timeout, power_threshold) as stream:
            responses = stream.transcribe()
            if responses is not None:
                listen_print_loop(responses)
        print("")


if __name__ == "__main__":
    main()
