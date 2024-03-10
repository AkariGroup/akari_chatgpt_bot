import io
import json
import time
import wave
from queue import Queue
from threading import Thread
from typing import Any

import pyaudio
import requests

from .err_handler import ignoreStderr


class TextToVoiceVox(object):
    def __init__(self, host: str = "127.0.0.1", port: str = "52001") -> None:
        self.queue: Queue[str] = Queue()
        self.host = host
        self.port = port
        self.play_flg = False
        self.finished = True
        self.voice_thread = Thread(target=self.text_to_voice_thread)
        self.voice_thread.start()

    def __exit__(self) -> None:
        self.voice_thread.join()

    def text_to_voice_thread(self) -> None:
        while True:
            if self.queue.qsize() > 0 and self.play_flg:
                text = self.queue.get()
                self.text_to_voice(text)
            if self.queue.qsize() == 0:
                self.finished = True

    def put_text(
        self, text: str, play_now: bool = True, blocking: bool = False
    ) -> None:
        if play_now:
            self.play_flg = True
        self.queue.put(text)
        self.finished = False
        if blocking:
            while not self.finished:
                time.sleep(0.01)

    def wait_finish(self) -> None:
        while not self.finished:
            time.sleep(0.01)

    def post_audio_query(
        self,
        text: str,
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
        address = "http://" + self.host + ":" + self.port + "/audio_query"
        res = requests.post(address, params=params)
        return res.json()

    def post_synthesis(
        self,
        audio_query_response: dict,
    ) -> bytes:
        params = {"speaker": 8}
        headers = {"content-type": "application/json"}
        audio_query_response_json = json.dumps(audio_query_response)
        address = "http://" + self.host + ":" + self.port + "/synthesis"
        res = requests.post(
            address, data=audio_query_response_json, params=params, headers=headers
        )
        return res.content

    def play_wav(self, wav_file: bytes) -> None:
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
            while data and self.play_flg:
                stream.write(data)
                data = wr.readframes(chunk)
            time.sleep(0.2)
            stream.close()
        p.terminate()

    def text_to_voice(self, text: str) -> None:
        res = self.post_audio_query(text)
        wav = self.post_synthesis(res)
        self.play_wav(wav)


class TextToVoiceVoxWeb(TextToVoiceVox):
    def __init__(self, apikey: str) -> None:
        self.queue: Queue[str] = Queue()
        self.apikey = apikey
        self.play_flg = False
        self.voice_thread = Thread(target=self.text_to_voice_thread)
        self.voice_thread.start()

    def text_to_voice_thread(self) -> None:
        while True:
            if self.queue.qsize() > 0 and self.play_flg:
                text = self.queue.get()
                self.text_to_voice(text)

    def post_web(
        self,
        text: str,
        speaker: int = 8,
        pitch: int = 0,
        intonation_scale: int = 1,
        speed: int = 1,
    ) -> bytes:
        address = (
            "https://deprecatedapis.tts.quest/v2/voicevox/audio/?key="
            + self.apikey
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

    def text_to_voice(self, text: str) -> None:
        wav = self.post_web(text=text)
        self.play_wav(wav)
