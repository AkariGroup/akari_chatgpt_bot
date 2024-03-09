
# akari_chatgpt_bot
音声認識、文章生成、音声合成を使って対話するチャットボットアプリです。  

![概要図](jpg/akari_chatgpt_bot.jpg "概要図")

## 動作確認済み環境
AKARI上で動作確認済み。  
`chatbot_akari.py`以外はUbuntu22.04環境であれば使用可能です。  

## セットアップ
1. submoduleの更新  
`git submodule update --init`  

1. ライブラリのインストール  
`sudo apt install python3.10 python3.10-venv portaudio19-dev gnome-terminal`  

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

1. (Claudeの文章生成を使う場合)OPENAI KEYの作成   
[ANTHROPIC](https://www.anthropic.com/)にてユーザ登録しAPI KEYを作成し、~/.bashrcに自身のkeyを記述  
`export ANTHROPIC_API_KEY_API_KEY=sk-xxxxxxxxxxxxxxx`  

1. (音声合成をweb版で使う場合) VOICEVOX web版のAPI KEYの作成
[WEB版VOICEVOX API（高速）](https://voicevox.su-shiki.com/su-shikiapis/) にてapikeyを作成し、~/.bashrcに自身のkeyを記述  
`export VOICEVOX_API_KEY='xxxxxxxxxxxxxxx`  

1. (音声合成をローカルで使う場合) VOICEVOXのダウンロード  
[VOICEVOX](https://voicevox.hiroshiba.jp/)をダウンロード、インストールし、起動しておく。  
AKARIなどで動かす場合は、下記の「VOICEVOXをOSS版で使いたい場合」の手順で同一ネットワーク内の外部PC上にサーバーを立てることを推奨。  

1. (AKARIのモーション再生を使う場合) akari_motion_serverのセットアップ  
`git clone https://github.com/AkariGroup/akari_motion_server`  
akari_motion_server内のREADME.mdに沿ってセットアップする。  

## VOICEVOXをOSS版で使いたい場合  
AKARIでVOICEVOXのローカル版を使う場合、AKARI本体内のCPUでVOICEVOXを実行すると処理時間がかかるので、リモートPC上(特にGPU版)でVOICVOXを実行することを推奨する。  
その場合下記を参考にOSS版を用いる。  

(GPUを使う場合)
`docker pull voicevox/voicevox_engine:nvidia-ubuntu20.04-latest`  
`docker run --rm --gpus all -p '{VOICEVOXを起動するPC自身のIPアドレス}:50021:50021' voicevox/voicevox_engine:nvidia-ubuntu20.04-latest`  

上記でVOICEVOXを起動した後、AKARI上で"--voicevox_host"にこのPCのIPアドレスを指定する。  

## 個別サンプルの実行

音声認識のサンプル  
マイクへの発話を文章に変換  
`python3 speech_to_text_example.py`  

chatGPTのサンプル  
キーボード入力した文章に対してchatGPTで返答を作成  
`python3 chatgpt_example.py`  

`python3 chatgpt_example.py -m gpt-3.5-turbo-0125 gpt-4-turbo-preview claude-3-sonnet-20240229 claude-3-opus-20240229`  


音声合成のサンプル  
キーボード入力した文章を音声合成で発話  
`python3 voicevox_example.py`  

## 音声対話の実行
実行後、ターミナルでEnterキーを押し、マイクに話しかけると返答が返ってくる。  

音声対話  
`python3 chatbot.py`  

音声対話+AKARIのモーション再生  
`python3 chatbot_akari.py`  

引数は下記が使用可能  
- `-t`,`--timeout`: マイク入力がこの時間しきい値以下になったら音声入力を打ち切る。デフォルトは0.5[s]。短いと応答が早くなるが不安定になりやすい。  
- `-p`,`--power_threshold`: マイク入力の音量しきい値。デフォルトは0で、0の場合アプリ起動時に周辺環境の音量を取得し、そこから音量しきい値を自動決定する。  
- `--voicevox_local`: このオプションをつけた場合、voicevoxのweb版ではなくローカル版を実行する。  
- `--voicevox_host`: `--voicevox_local`を有効にした場合、ここで指定したhostのvoicevoxにリクエストを送信する。デフォルトは"127.0.0.1"なのでlocalhostのvoicevoxを利用する。  
- `--voicevox_port`: `--voicevox_local`を有効にした場合、ここで指定したportのvoicevoxにリクエストを送信する。デフォルトは50021。  

## 遅延なし音声対話botの実行

### 概要

![遅延なし図解](jpg/faster_chatgpt_bot.jpg "遅延なし図解")

発話の最初の数文字を認識した時点で選択肢から返答を作成しておくことで、第一声を遅延なく返答する方法です。  

### 全体図

![構成図](jpg/faster_chatgpt_bot_system.jpg "構成図")

Google音声認識、chatGPT、Voicevoxとのやり取りをする各アプリは個別に動作しており、各アプリ間はgrpcで通信しています。  

### 起動方法

1. 上記 **VOICEVOXをOSS版で使いたい場合** の手順を元に、別PCでVoicevoxを起動しておく。  

2. (AKARIのモーション再生を行う場合)akari_motion_serverを起動する。  
   起動方法は https://github.com/AkariGroup/akari_motion_server を参照。  

3. `voicevox_server` を起動する。(Voicevoxへの送信サーバ)  
   `python3 voicevox_server.py`  

   引数は下記が使用可能  
   - `--voicevox_local`: このオプションをつけた場合、voicevoxのweb版ではなくローカル版を実行する。  
   - `--voicevox_host`: `--voicevox_local`を有効にした場合、ここで指定したhostのvoicevoxにリクエストを送信する。デフォルトは"127.0.0.1"なのでlocalhostのvoicevoxを利用する。  
   - `--voicevox_port`: `--voicevox_local`を有効にした場合、ここで指定したportのvoicevoxにリクエストを送信する。デフォルトは50021。  

4. `gpt_publisher`を起動する。(ChatGPTへリクエストを送信し、受信結果をvoicevox_serverへ渡す。)  
   `python3 gpt_publisher.py`  

   引数は下記が使用可能  
   - `--ip`: gpt_serverのIPアドレス。デフォルトは"127.0.0.1"
   - `--port`: gpt_serverのポート。デフォルトは"10001"

5. speech_publisher.pyを起動する。(Google音声認識の結果をgpt_publisherへ渡す。)  
   `python3 speech_publisher.py`  

   引数は下記が使用可能  
   - `--robot_ip`: akari_motion_serverのIPアドレス。デフォルトは"127.0.0.1"
   - `--robot_port`: akari_motion_serverのポート。デフォルトは"50055"
   - `--gpt_ip`: gpt_serverのIPアドレス。デフォルトは"127.0.0.1"
   - `--gpt_port`: gpt_serverのポート。デフォルトは"10001"
   - `--voicevox_ip`: voicevox_serverのIPアドレス。デフォルトは"127.0.0.1"
   - `--voicevox_port`: voicevox_serverのポート。デフォルトは"10002"
   - `-t`,`--timeout`: マイク入力がこの時間しきい値以下になったら音声入力を打ち切る。デフォルトは0.5[s]。短いと応答が早くなるが不安定になりやすい。  
   - `-p`,`--power_threshold`: マイク入力の音量しきい値。デフォルトは0で、0の場合アプリ起動時に周辺環境の音量を取得し、そこから音量しきい値を自動決定する。  
   - `--no_motion`: このオプションをつけた場合、音声入力中のうなずき動作を無効化する。  

6. `speech_publisher.py`のターミナルでEnterキーを押し、マイクに話しかけると返答が返ってくる。


### スクリプトで一括起動する方法

1. 上記 **VOICEVOXをOSS版で使いたい場合** の手順を元に、別PCでVoicevoxを起動しておく。  

2. スクリプトを実行する。  

   `cd script`  
   `./faster_chatbot.sh {1.でVoicevoxを起動したPCのIPアドレス} {akari_motion_serverのパス}`  

   akari_motion_serverのパスを入力しなければ、akari_motion_serverは起動せず、モーションの再生は行われません(AKARI以外でも使えます)。  

3. `speech_publisher.py`のターミナルでEnterキーを押し、マイクに話しかけると返答が返ってくる。

## その他
音声合成では、デフォルトの音声として「VOICEVOX:春日部つむぎ」を使用しています。  
