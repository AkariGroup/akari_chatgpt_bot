import base64
from typing import Optional, List
import numpy as np
import cv2
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json
from pydantic import BaseModel
from lib.chat_akari import ChatStreamAkari


app = FastAPI()

# CORSミドルウェアを追加
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chat_akari = ChatStreamAkari()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = "gpt-4o"
    temperature: Optional[float] = 0.7


class VisionChatRequest(BaseModel):
    text: str
    model: Optional[str] = "gpt-4o"
    temperature: Optional[float] = 0.7
    image_width: Optional[int] = 480
    image_height: Optional[int] = 270


def process_base64_image(base64_str: str) -> np.ndarray:
    try:
        img_data = base64.b64decode(base64_str)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Failed to decode image")
        return img
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image data: {str(e)}")


@app.get("/chat")
async def chat_get(
    messages: str = Query(...),
    model: str = Query(default="gpt-4o"),
    temperature: float = Query(default=0.7)
):
    try:
        # JSON文字列をパース
        messages_data = json.loads(messages)

        # チャット応答のストリーミング
        async def generate():
            for response in chat_akari.chat(
                messages=messages_data,
                model=model,
                temperature=temperature
            ):
                yield f"data: {json.dumps({'content': response})}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chat_and_motion")
async def chat_and_motion_get(
    messages: str = Query(...),
    model: str = Query(default="gpt-4o"),
    temperature: float = Query(default=0.7)
):
    try:
        # JSON文字列をパース
        messages_data = json.loads(messages)

        # チャットと動作応答のストリーミング
        async def generate():
            for response in chat_akari.chat_and_motion(
                messages=messages_data,
                model=model,
                temperature=temperature
            ):
                yield f"data: {json.dumps({'content': response})}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # メッセージをdict形式に変換
        messages = [
            {"role": msg.role, "content": msg.content} for msg in request.messages
        ]

        # チャット応答のストリーミング
        async def generate():
            for response in chat_akari.chat(
                messages=messages,
                model=request.model,
                temperature=request.temperature
            ):
                yield f"data: {json.dumps({'content': response})}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat_and_motion")
async def chat_and_motion(request: ChatRequest):
    try:
        # メッセージをdict形式に変換
        messages = [
            {"role": msg.role, "content": msg.content} for msg in request.messages
        ]

        # チャットと動作応答のストリーミング
        async def generate():
            for response in chat_akari.chat_and_motion(
                messages=messages,
                model=request.model,
                temperature=request.temperature
            ):
                yield f"data: {json.dumps({'content': response})}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat_with_vision")
async def chat_with_vision(
    request: VisionChatRequest,
    file: UploadFile = File(...)
):
    try:
        # アップロードされた画像の読み込み
        image_data = await file.read()
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image data")

        # 画像付きメッセージの作成
        vision_message = chat_akari.create_vision_message(
            text=request.text,
            image=image,
            model=request.model,
            image_width=request.image_width,
            image_height=request.image_height
        )
        messages = [vision_message]

        # チャット応答のストリーミング
        async def generate():
            for response in chat_akari.chat(
                messages=messages,
                model=request.model,
                temperature=request.temperature
            ):
                yield f"data: {json.dumps({'content': response})}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
