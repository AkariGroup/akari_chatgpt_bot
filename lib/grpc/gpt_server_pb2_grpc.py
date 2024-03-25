# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import gpt_server_pb2 as gpt__server__pb2


class GptServerServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.SetGpt = channel.unary_unary(
                '/gpt_server.GptServerService/SetGpt',
                request_serializer=gpt__server__pb2.SetGptRequest.SerializeToString,
                response_deserializer=gpt__server__pb2.SetGptReply.FromString,
                )
        self.InterruptGpt = channel.unary_unary(
                '/gpt_server.GptServerService/InterruptGpt',
                request_serializer=gpt__server__pb2.InterruptGptRequest.SerializeToString,
                response_deserializer=gpt__server__pb2.InterruptGptReply.FromString,
                )
        self.SendMotion = channel.unary_unary(
                '/gpt_server.GptServerService/SendMotion',
                request_serializer=gpt__server__pb2.SendMotionRequest.SerializeToString,
                response_deserializer=gpt__server__pb2.SendMotionReply.FromString,
                )


class GptServerServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def SetGpt(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def InterruptGpt(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SendMotion(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_GptServerServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'SetGpt': grpc.unary_unary_rpc_method_handler(
                    servicer.SetGpt,
                    request_deserializer=gpt__server__pb2.SetGptRequest.FromString,
                    response_serializer=gpt__server__pb2.SetGptReply.SerializeToString,
            ),
            'InterruptGpt': grpc.unary_unary_rpc_method_handler(
                    servicer.InterruptGpt,
                    request_deserializer=gpt__server__pb2.InterruptGptRequest.FromString,
                    response_serializer=gpt__server__pb2.InterruptGptReply.SerializeToString,
            ),
            'SendMotion': grpc.unary_unary_rpc_method_handler(
                    servicer.SendMotion,
                    request_deserializer=gpt__server__pb2.SendMotionRequest.FromString,
                    response_serializer=gpt__server__pb2.SendMotionReply.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'gpt_server.GptServerService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class GptServerService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def SetGpt(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/gpt_server.GptServerService/SetGpt',
            gpt__server__pb2.SetGptRequest.SerializeToString,
            gpt__server__pb2.SetGptReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def InterruptGpt(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/gpt_server.GptServerService/InterruptGpt',
            gpt__server__pb2.InterruptGptRequest.SerializeToString,
            gpt__server__pb2.InterruptGptReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SendMotion(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/gpt_server.GptServerService/SendMotion',
            gpt__server__pb2.SendMotionRequest.SerializeToString,
            gpt__server__pb2.SendMotionReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
