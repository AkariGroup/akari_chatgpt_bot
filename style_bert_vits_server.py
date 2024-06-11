import argparse
import os
import sys
import time
from concurrent import futures

import grpc
from lib.style_bert_vits import TextToStyleBertVits

sys.path.append(os.path.join(os.path.dirname(__file__), "lib/grpc"))
import style_bert_vits_server_pb2_grpc
import style_bert_vits_server_pb2


class StyleBertVitsServer(style_bert_vits_server_pb2_grpc.StyleBertVitsServerServiceServicer):
    """
    StyleBertVitsにtextを送信し、音声を再生するgprcサーバ
    """

    def __init__(self, text_to_voice) -> None:
        self.text_to_voice = text_to_voice

    def SetText(
        self,
        request: style_bert_vits_server_pb2.SetTextRequest(),
        context: grpc.ServicerContext,
    ) -> style_bert_vits_server_pb2.SetTextReply:
        # 即時再生しないようにis_playはFalseで実行
        print(f"Send text: {request.text}")
        self.text_to_voice.put_text(request.text, play_now=False)
        return style_bert_vits_server_pb2.SetTextReply(success=True)

    def SetParam(
        self,
        request: style_bert_vits_server_pb2.SetParamRequest(),
        context: grpc.ServicerContext,
    ) -> style_bert_vits_server_pb2.SetParamReply:
        if request.model_name:
            self.text_to_voice.set_param(model_name=request.model_name)
        if request.length:
            self.text_to_voice.set_param(length=request.length)
        if request.style:
            self.text_to_voice.set_param(style=request.style)
        if request.style_weight:
            self.text_to_voice.set_param(style_weight=request.style_weight)
        return style_bert_vits_server_pb2.SetParamReply(success=True)

    def InterruptVoice(
        self,
        request: style_bert_vits_server_pb2.InterruptVoiceRequest(),
        context: grpc.ServicerContext,
    ) -> style_bert_vits_server_pb2.InterruptVoiceReply:
        while not self.text_to_voice.queue.empty():
            self.text_to_voice.queue.get()
        return style_bert_vits_server_pb2.InterruptVoiceReply(success=True)

    def SetVoicePlayFlg(
        self,
        request: style_bert_vits_server_pb2.SetVoicePlayFlgRequest(),
        context: grpc.ServicerContext,
    ) -> style_bert_vits_server_pb2.SetVoicePlayFlgReply:
        self.text_to_voice.play_flg = request.flg
        return style_bert_vits_server_pb2.SetVoicePlayFlgReply(success=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--voice_host",
        type=str,
        default="127.0.0.1",
        help="Style-Bert-VITS2 server host",
    )
    parser.add_argument(
        "--voice_port",
        type=str,
        default="5000",
        help="Style-Bert-VITS2 server port",
    )
    args = parser.parse_args()

    host = args.voice_host
    port = args.voice_port
    text_to_voice = TextToStyleBertVits(host, port)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    style_bert_vits_server_pb2_grpc.add_StyleBertVitsServerServiceServicer_to_server(
        StyleBertVitsServer(text_to_voice), server
    )
    port = "10002"
    server.add_insecure_port("[::]:" + port)
    server.start()
    print(f"style_bert_vits_server start. port: {port}")
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        exit()


if __name__ == "__main__":
    main()
