
# akari_chatgpt_bot
音声認識、文章生成、音声合成を使って対話するチャットボットアプリです。

![概要図](jpg/akari_chatgpt_bot.jpg "概要図")

## 動作確認済み環境
AKARI上で動作確認済み。  
`main_akari.py`以外はUbuntu22.04環境であれば使用可能です。  

## セットアップ
1. submoduleの更新  
`git submodule update --init`  

1. ライブラリのインストール  
`sudo apt install python3.10 python3.10-venv portaudio19-dev`  

1. 仮想環境の作成  
`python3 -m venv venv`  
`. venv/bin/activate`  
`pip install -r requirements.txt`  

1. (音声認識を使う場合) Cloud Speech-to-Text APIの有効化、秘密鍵ダウンロード  
Google cloud consoleに登録し、Cloud Speech-to-Text APIを有効化する。  
認証用のjsonをダウンロードし、~/.bashrcにパスを記述  
`export GOOGLE_APPLICATION_CREDENTIALS=/home/xxx/xxx.json`  

1. (chatGPTの文章生成を使う場合)OPENAI KEYの作成   
[OPENAI](https://openai.com/)にてユーザ登録しAPI KEYを作成し、~/.bashrcに自身のkeyを記述  
`export OPENAI_API_KEY=sk-xxxxxxxxxxxxxxx`  

1. (音声合成をweb版で使う場合) VOICEVOX web版のAPI KEYの作成
[WEB版VOICEVOX API（高速）](https://voicevox.su-shiki.com/su-shikiapis/) にてapikeyを作成し、~/.bashrcに自身のkeyを記述  
`export VOICEVOX_API_KEY='xxxxxxxxxxxxxxx`  

1. (音声合成をローカルで使う場合) VOICEVOXのダウンロード  
[VOICEVOX](https://voicevox.hiroshiba.jp/)をダウンロード、インストールし、起動しておく。  
AKARIなどで動かす場合は、下記の「VOICEVOXをOSS版で使いたい場合」の手順で同一ネットワーク内の外部PC上にサーバーを立てることを推奨。  

1. (AKARIのモーション再生を使う場合) akari_motion_serverのセットアップ  
`git clone https://github.com/AkariGroup/akari_motion_server`  
akari_motion_server内のREADME.mdに沿ってセットアップする。  


## 個別サンプルの実行

音声認識のサンプル  
マイクへの発話を文章に変換  
`python3 speech_to_text_example.py`  

chatGPTのサンプル  
キーボード入力した文章に対してchatGPTで返答を作成  
`python3 chat_example.py`  

音声合成のサンプル  
キーボード入力した文章を音声合成で発話  
`python3 voicevox_example.py`  

## 音声対話の実行

音声対話  
`python3 main.py`  

音声対話+AKARIのモーション再生  
`python3 main_akari.py`  

引数は下記が使用可能  
- `-t`,`--timeout`: マイク入力がこの時間しきい値以下になったら音声入力を打ち切る。デフォルトは0.5[s]。短いと応答が早くなるが不安定になりやすい。  
- `-p`,`--power_threshold`: マイク入力の音量しきい値。デフォルトは0で、0の場合アプリ起動時に周辺環境の音量を取得し、そこから音量しきい値を自動決定する。  
- `--voicevox_local`: このオプションをつけた場合、voicevoxのweb版ではなくローカル版を実行する。  
- `--voicevox_host`: `--voicevox_local`を有効にした場合、ここで指定したhostのvoicevoxにリクエストを送信する。デフォルトは"127.0.0.1"なのでlocalhostのvoicevoxを利用する。  
- `--voicevox_port`: `--voicevox_local`を有効にした場合、ここで指定したportのvoicevoxにリクエストを送信する。デフォルトは50021。  

## VOICEVOXをOSS版で使いたい場合  
AKARIでVOICEVOXのローカル版を使う場合、AKARI本体内のCPUでVOICEVOXを実行すると処理時間がかかるので、リモートPC上(特にGPU版)でVOICVOXを実行することを推奨する。
その場合下記を参考にOSS版を用いる。  

(GPUを使う場合)cuda,cudnnをインストール  
`git clone https://github.com/VOICEVOX/voicevox_engine.git`  
`git clone https://github.com/VOICEVOX/voicevox_core`  
`sudo apt install python3.11 python3.11-dev python3.11-venv`  
`cd voicevox_engine`  
`python3.11 -m venv venv`  
`. venv/bin/activate`  
`pip install -r requirements.txt`  
`export LD_LIBRARY_PATH="voicevox_coreへのパス":$LD_LIBRARY_PATH`  
`python3 run.py --use_gpu --voicelib_dir "voicevox_coreへのパス" --runtime_dir "voicevox_coreへのパス" --host "VOICEVOXを起動するPC自身のIPアドレス"`

上記でVOICEVOXを起動した後、AKARI上で"--voicevox_host"にこのPCのIPアドレスを指定する。

## その他
音声合成では、デフォルトの音声として「VOICEVOX:春日部つむぎ」を使用しています。
