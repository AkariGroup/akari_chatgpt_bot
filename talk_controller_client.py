import argparse
import os
import sys
import time

import grpc

sys.path.append(os.path.join(os.path.dirname(__file__), "lib/grpc"))
import speech_server_pb2
import speech_server_pb2_grpc
import voice_server_pb2
import voice_server_pb2_grpc


def main() -> None:
    global enable_input
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--speech_ip", help="speech publisher ip address", default="127.0.0.1", type=str
    )
    parser.add_argument(
        "--speech_port", help="speech publisher port number", default="10003", type=str
    )
    parser.add_argument(
        "--voice_ip", help="Voice server ip address", default="127.0.0.1", type=str
    )
    parser.add_argument(
        "--voice_port", help="Voice server port number", default="10002", type=str
    )
    args = parser.parse_args()

    # grpc stubの設定
    speech_channel = grpc.insecure_channel(args.speech_ip + ":" + str(args.speech_port))
    voice_channel = grpc.insecure_channel(args.voice_ip + ":" + args.voice_port)
    voice_stub = None
    speech_stub = None
    # Voice serverの接続確認
    while True:
        try:
            grpc.channel_ready_future(voice_channel).result(timeout=0.5)
            voice_stub = voice_server_pb2_grpc.VoiceServerServiceStub(voice_channel)
            break
        except grpc.FutureTimeoutError:
            print("Connecting to voice server timeout. Retrying")
            continue
        except KeyboardInterrupt:
            return
        except BaseException as e:
            print(f"RPC error: {e}")
            continue
    print("Connected to voice server")
    # Speech serverの接続確認
    while True:
        try:
            grpc.channel_ready_future(speech_channel).result(timeout=0.5)
            speech_stub = speech_server_pb2_grpc.SpeechServerServiceStub(speech_channel)
            break
        except grpc.FutureTimeoutError:
            print("Connecting to speech server timeout. Retrying")
            continue
        except KeyboardInterrupt:
            return
        except BaseException as e:
            print(f"RPC error: {e}")
            continue
    print("Connected to speech server")
    is_voice_playing = False

    while True:
        if not is_voice_playing:
            try:
                ret = voice_stub.IsVoicePlaying(
                    voice_server_pb2.IsVoicePlayingRequest()
                )
                is_voice_playing = ret.is_playing
            except KeyboardInterrupt:
                return
            except BaseException:
                print("Voice server connection error!")
            if is_voice_playing:
                speech_stub.ToggleSpeech(
                    speech_server_pb2.ToggleSpeechRequest(enable=False)
                )
        else:
            try:
                ret = voice_stub.IsVoicePlaying(
                    voice_server_pb2.IsVoicePlayingRequest()
                )
                is_voice_playing = ret.is_playing
            except KeyboardInterrupt:
                return
            except BaseException:
                print("Voice server connection error!")
            if not is_voice_playing:
                speech_stub.ToggleSpeech(
                    speech_server_pb2.ToggleSpeechRequest(enable=True)
                )
        time.sleep(0.1)


if __name__ == "__main__":
    main()
