#!/bin/bash
# -*- coding: utf-8 -*-
## シェルオプション
set -e           # コマンド実行に失敗したらエラー
set -u           # 未定義の変数にアクセスしたらエラー
set -o pipefail  # パイプのコマンドが失敗したらエラー（bashのみ）

ip=$1

echo ${ip}

(
cd ~/akari_motion_server
 . venv/bin/activate
 gnome-terminal --title="motion_server"-- bash -ic "python3 server.py"
)

(
 . venv/bin/activate

 gnome-terminal --title="voicevox_server" -- bash -ic "python3 voicevox_server.py --voicevox_local --voicevox_host ${ip}"
 gnome-terminal --title="gpt_to_voice_publlisher" -- bash -ic "python3 gpt_to_voice_publlisher.py"
 gnome-terminal --title="speech_to_text_publisher" -- bash -ic "python3 speech_to_text_publisher.py"
)
