# Chat Akari Web API

Chat AkariライブラリのWeb APIインターフェース。

## セットアップ

1. 依存パッケージのインストール:
```bash
pip install -r requirements.txt
```

2. サーバーの起動:
```bash
python server.py
```

サーバーは `http://localhost:8000` で起動します。

## API エンドポイント

### 1. `/chat` - テキストチャット

通常のテキストチャットを行うエンドポイント。

```python
import requests
import json

response = requests.post(
    "http://localhost:8000/chat",
    json={
        "messages": [
            {
                "role": "user",
                "content": "こんにちは"
            }
        ],
        "model": "gpt-4o",
        "temperature": 0.7
    },
    stream=True
)

# Server-Sent Eventsの処理
for line in response.iter_lines():
    if line:
        # 'data: ' プレフィックスを除去してJSONをパース
        data = json.loads(line.decode('utf-8').split('data: ')[1])
        print(data['content'], end='', flush=True)
```

### 2. `/chat_and_motion` - モーション付きチャット

チャット応答とモーション制御を組み合わせたエンドポイント。

```python
response = requests.post(
    "http://localhost:8000/chat_and_motion",
    json={
        "messages": [
            {
                "role": "user",
                "content": "こんにちは"
            }
        ],
        "model": "gpt-4o",
        "temperature": 0.7
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        data = json.loads(line.decode('utf-8').split('data: ')[1])
        print(data['content'], end='', flush=True)
```

### 3. `/chat_with_vision` - 画像付きチャット

画像を含むチャットを行うエンドポイント。

```python
import requests
from pathlib import Path

with open('image.jpg', 'rb') as f:
    files = {'file': ('image.jpg', f, 'image/jpeg')}
    response = requests.post(
        "http://localhost:8000/chat_with_vision",
        data={
            'text': 'この画像について説明してください',
            'model': 'gpt-4-vision-preview',
            'temperature': 0.7,
            'image_width': 480,
            'image_height': 270
        },
        files=files,
        stream=True
    )

    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode('utf-8').split('data: ')[1])
            print(data['content'], end='', flush=True)
```

## レスポンス形式

すべてのエンドポイントはServer-Sent Events (SSE)形式でストリーミングレスポンスを返します。各レスポンスは以下の形式のJSONデータです：

```json
{
    "content": "生成されたテキストの一部"
}
```

## 注意事項

- 必要なAPIキー（OpenAI、Anthropic、Gemini）は環境変数として設定されている必要があります。
- モーション制御を使用する場合は、akari_motion_serverが起動している必要があります。
- Vision機能を使用する場合は、対応したモデル（例：gpt-4-vision-preview）を指定する必要があります。
