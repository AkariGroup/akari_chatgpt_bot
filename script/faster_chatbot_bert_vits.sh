#!/bin/bash
# -*- coding: utf-8 -*-
## シェルオプション
set -e           # コマンド実行に失敗したらエラー
set -u           # 未定義の変数にアクセスしたらエラー
set -o pipefail  # パイプのコマンドが失敗したらエラー（bashのみ）

ip=$1

echo ${ip}

#第２引数でakari_motion_serverのパスが記載されていた場合は、そちらも起動する。
if [ "$#" -ge 2 ]; then
    (
    cd $2
    . venv/bin/activate
    gnome-terminal --title="motion_server" -- bash -ic "python3 server.py"
    )
fi


(
cd ../
 . venv/bin/activate
 gnome-terminal --title="style_bert_vits_server" -- bash -ic "python3 style_bert_vits_server.py --voice_host ${ip}"
 gnome-terminal --title="gpt_publisher" -- bash -ic "python3 gpt_publisher.py"
 gnome-terminal --title="speech_publisher" -- bash -ic "python3 speech_publisher.py --timeout 0.8"
)
