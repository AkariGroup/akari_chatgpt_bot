from typing import Any, Generator

import numpy as np
import cv2
import openai

last_char = ["、", "。", ".", "！", "？", "\n"]


def create_message(text: str, role: str = "user") -> str:
    message = {"role": role, "content": text}
    return message


def cv_to_base64(image: np.ndarray) -> str:
    _, encoded = cv2.imencode(".jpg", image)
    return base64.b64encode(encoded).decode("ascii")


def create_vision_message(text: str, image: np.ndarray) -> str:
    resized_image = cv2.resize(image, (320, 240))
    base64_image = cv_to_base64(resized_image)
    url = f"data:image/jpeg;base64,{base64_image}"
    message = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": text,
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": url,
                },
            },
        ],
    }
    return message


def chat(
    messages: list, model: str = "gpt-3.5-turbo-0613", temperature: float = 0.7
) -> Any:
    result = openai.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=messages,
    )
    response_text = result["choices"][0]["message"]["content"]
    return response_text


def chat_stream(
    messages: list, model: str = "gpt-3.5-turbo-0613", temperature: float = 0.7
) -> Generator[str, None, None]:
    result = openai.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=1024,
        n=1,
        stream=True,
        temperature=temperature,
        stop=None,
    )
    fullResponse = ""
    RealTimeResponce = ""
    for chunk in result:
        text = chunk.choices[0].delta.content
        if text is None:
            pass
        else:
            fullResponse += text
            RealTimeResponce += text

            for index, char in enumerate(RealTimeResponce):
                if char in last_char:
                    pos = index + 2  # 区切り位置
                    sentence = RealTimeResponce[:pos]  # 1文の区切り
                    RealTimeResponce = RealTimeResponce[pos:]  # 残りの部分
                    # 1文完成ごとにテキストを読み上げる(遅延時間短縮のため)
                    yield sentence
                    break
                else:
                    pass
