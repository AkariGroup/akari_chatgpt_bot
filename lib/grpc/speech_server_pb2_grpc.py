# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import speech_server_pb2 as speech__server__pb2


class SpeechServerServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.ToggleSpeech = channel.unary_unary(
                '/speech_server.SpeechServerService/ToggleSpeech',
                request_serializer=speech__server__pb2.ToggleSpeechRequest.SerializeToString,
                response_deserializer=speech__server__pb2.ToggleSpeechReply.FromString,
                )


class SpeechServerServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def ToggleSpeech(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_SpeechServerServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'ToggleSpeech': grpc.unary_unary_rpc_method_handler(
                    servicer.ToggleSpeech,
                    request_deserializer=speech__server__pb2.ToggleSpeechRequest.FromString,
                    response_serializer=speech__server__pb2.ToggleSpeechReply.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'speech_server.SpeechServerService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class SpeechServerService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def ToggleSpeech(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/speech_server.SpeechServerService/ToggleSpeech',
            speech__server__pb2.ToggleSpeechRequest.SerializeToString,
            speech__server__pb2.ToggleSpeechReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
