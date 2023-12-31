import io
import json
import wave
from queue import Queue
from threading import Thread
from time import sleep
from typing import Any

import pyaudio
import requests

from .err_handler import ignoreStderr


def post_audio_query(
    text: str,
    host: str = "127.0.0.1",
    port: str = "50021",
    speaker: int = 8,
    speed_scale: float = 1.0,
) -> Any:
    params = {
        "text": text,
        "speaker": speaker,
        "speed_scale": speed_scale,
        "pre_phoneme_length": 0,
        "post_phoneme_length": 0,
    }
    address = "http://" + host + ":" + port + "/audio_query"
    res = requests.post(address, params=params)
    return res.json()


def post_synthesis(
    audio_query_response: dict, host: str = "127.0.0.1", port: str = "50021"
) -> bytes:
    params = {"speaker": 8}
    headers = {"content-type": "application/json"}
    audio_query_response_json = json.dumps(audio_query_response)
    address = "http://" + host + ":" + port + "/synthesis"
    res = requests.post(
        address, data=audio_query_response_json, params=params, headers=headers
    )
    return res.content


def play_wav(wav_file: bytes) -> None:
    wr: wave.Wave_read = wave.open(io.BytesIO(wav_file))
    with ignoreStderr():
        p = pyaudio.PyAudio()
        stream = p.open(
            format=p.get_format_from_width(wr.getsampwidth()),
            channels=wr.getnchannels(),
            rate=wr.getframerate(),
            output=True,
        )
        chunk = 1024
        data = wr.readframes(chunk)
        while data:
            stream.write(data)
            data = wr.readframes(chunk)
        sleep(0.5)
        stream.close()
    p.terminate()


def text_to_voice(text: str, host: str = "127.0.0.1", port: str = "52001") -> None:
    res = post_audio_query(text, host, port)
    wav = post_synthesis(res, host, port)
    play_wav(wav)


def post_web(
    apikey: str,
    text: str,
    speaker: int = 8,
    pitch: int = 0,
    intonation_scale: int = 1,
    speed: int = 1,
) -> bytes:
    address = (
        "https://deprecatedapis.tts.quest/v2/voicevox/audio/?key="
        + apikey
        + "&speaker="
        + str(speaker)
        + "&pitch="
        + str(pitch)
        + "&intonationScale="
        + str(intonation_scale)
        + "&speed="
        + str(speed)
        + "&text="
        + text
    )
    res = requests.post(address)
    return res.content


def text_to_voice_web(apikey: str, text: str) -> None:
    wav = post_web(apikey=apikey, text=text)
    play_wav(wav)


class TextToVoiceVox(object):
    def __init__(self, host: str = "127.0.0.1", port: str = "52001") -> None:
        self.queue: Queue[str] = Queue()
        self.host = host
        self.port = port
        self.voice_thread = Thread(target=self.text_to_voice_thread)
        self.voice_thread.start()

    def __exit__(self) -> None:
        self.voice_thread.join()

    def text_to_voice_thread(self) -> None:
        while True:
            if self.queue.qsize() > 0:
                text = self.queue.get()
                text_to_voice(text, self.host, self.port)

    def put_text(self, text: str) -> None:
        self.queue.put(text)


class TextToVoiceVoxWeb(object):
    def __init__(self, apikey: str) -> None:
        self.queue: Queue[str] = Queue()
        self.apikey = apikey
        self.voice_thread = Thread(target=self.text_to_voice_thread)
        self.voice_thread.start()

    def __exit__(self) -> None:
        self.voice_thread.join()

    def text_to_voice_thread(self) -> None:
        while True:
            if self.queue.qsize() > 0:
                text = self.queue.get()
                text_to_voice_web(apikey=self.apikey, text=text)

    def put_text(self, text: str) -> None:
        self.queue.put(text)
