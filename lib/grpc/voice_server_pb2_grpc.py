# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import voice_server_pb2 as voice__server__pb2


class VoiceServerServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.SetText = channel.unary_unary(
                '/voice_server.VoiceServerService/SetText',
                request_serializer=voice__server__pb2.SetTextRequest.SerializeToString,
                response_deserializer=voice__server__pb2.SetTextReply.FromString,
                )
        self.SetStyleBertVitsParam = channel.unary_unary(
                '/voice_server.VoiceServerService/SetStyleBertVitsParam',
                request_serializer=voice__server__pb2.SetStyleBertVitsParamRequest.SerializeToString,
                response_deserializer=voice__server__pb2.SetStyleBertVitsParamReply.FromString,
                )
        self.SetVoicevoxParam = channel.unary_unary(
                '/voice_server.VoiceServerService/SetVoicevoxParam',
                request_serializer=voice__server__pb2.SetVoicevoxParamRequest.SerializeToString,
                response_deserializer=voice__server__pb2.SetVoicevoxParamReply.FromString,
                )
        self.SetAivisParam = channel.unary_unary(
                '/voice_server.VoiceServerService/SetAivisParam',
                request_serializer=voice__server__pb2.SetAivisParamRequest.SerializeToString,
                response_deserializer=voice__server__pb2.SetAivisParamReply.FromString,
                )
        self.InterruptVoice = channel.unary_unary(
                '/voice_server.VoiceServerService/InterruptVoice',
                request_serializer=voice__server__pb2.InterruptVoiceRequest.SerializeToString,
                response_deserializer=voice__server__pb2.InterruptVoiceReply.FromString,
                )
        self.EnableVoicePlay = channel.unary_unary(
                '/voice_server.VoiceServerService/EnableVoicePlay',
                request_serializer=voice__server__pb2.EnableVoicePlayRequest.SerializeToString,
                response_deserializer=voice__server__pb2.EnableVoicePlayReply.FromString,
                )
        self.DisableVoicePlay = channel.unary_unary(
                '/voice_server.VoiceServerService/DisableVoicePlay',
                request_serializer=voice__server__pb2.DisableVoicePlayRequest.SerializeToString,
                response_deserializer=voice__server__pb2.DisableVoicePlayReply.FromString,
                )
        self.IsVoicePlaying = channel.unary_unary(
                '/voice_server.VoiceServerService/IsVoicePlaying',
                request_serializer=voice__server__pb2.IsVoicePlayingRequest.SerializeToString,
                response_deserializer=voice__server__pb2.IsVoicePlayingReply.FromString,
                )
        self.SentenceEnd = channel.unary_unary(
                '/voice_server.VoiceServerService/SentenceEnd',
                request_serializer=voice__server__pb2.SentenceEndRequest.SerializeToString,
                response_deserializer=voice__server__pb2.SentenceEndReply.FromString,
                )
        self.StartHeadControl = channel.unary_unary(
                '/voice_server.VoiceServerService/StartHeadControl',
                request_serializer=voice__server__pb2.StartHeadControlRequest.SerializeToString,
                response_deserializer=voice__server__pb2.StartHeadControlReply.FromString,
                )


class VoiceServerServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def SetText(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SetStyleBertVitsParam(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SetVoicevoxParam(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SetAivisParam(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def InterruptVoice(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def EnableVoicePlay(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DisableVoicePlay(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def IsVoicePlaying(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SentenceEnd(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def StartHeadControl(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_VoiceServerServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'SetText': grpc.unary_unary_rpc_method_handler(
                    servicer.SetText,
                    request_deserializer=voice__server__pb2.SetTextRequest.FromString,
                    response_serializer=voice__server__pb2.SetTextReply.SerializeToString,
            ),
            'SetStyleBertVitsParam': grpc.unary_unary_rpc_method_handler(
                    servicer.SetStyleBertVitsParam,
                    request_deserializer=voice__server__pb2.SetStyleBertVitsParamRequest.FromString,
                    response_serializer=voice__server__pb2.SetStyleBertVitsParamReply.SerializeToString,
            ),
            'SetVoicevoxParam': grpc.unary_unary_rpc_method_handler(
                    servicer.SetVoicevoxParam,
                    request_deserializer=voice__server__pb2.SetVoicevoxParamRequest.FromString,
                    response_serializer=voice__server__pb2.SetVoicevoxParamReply.SerializeToString,
            ),
            'SetAivisParam': grpc.unary_unary_rpc_method_handler(
                    servicer.SetAivisParam,
                    request_deserializer=voice__server__pb2.SetAivisParamRequest.FromString,
                    response_serializer=voice__server__pb2.SetAivisParamReply.SerializeToString,
            ),
            'InterruptVoice': grpc.unary_unary_rpc_method_handler(
                    servicer.InterruptVoice,
                    request_deserializer=voice__server__pb2.InterruptVoiceRequest.FromString,
                    response_serializer=voice__server__pb2.InterruptVoiceReply.SerializeToString,
            ),
            'EnableVoicePlay': grpc.unary_unary_rpc_method_handler(
                    servicer.EnableVoicePlay,
                    request_deserializer=voice__server__pb2.EnableVoicePlayRequest.FromString,
                    response_serializer=voice__server__pb2.EnableVoicePlayReply.SerializeToString,
            ),
            'DisableVoicePlay': grpc.unary_unary_rpc_method_handler(
                    servicer.DisableVoicePlay,
                    request_deserializer=voice__server__pb2.DisableVoicePlayRequest.FromString,
                    response_serializer=voice__server__pb2.DisableVoicePlayReply.SerializeToString,
            ),
            'IsVoicePlaying': grpc.unary_unary_rpc_method_handler(
                    servicer.IsVoicePlaying,
                    request_deserializer=voice__server__pb2.IsVoicePlayingRequest.FromString,
                    response_serializer=voice__server__pb2.IsVoicePlayingReply.SerializeToString,
            ),
            'SentenceEnd': grpc.unary_unary_rpc_method_handler(
                    servicer.SentenceEnd,
                    request_deserializer=voice__server__pb2.SentenceEndRequest.FromString,
                    response_serializer=voice__server__pb2.SentenceEndReply.SerializeToString,
            ),
            'StartHeadControl': grpc.unary_unary_rpc_method_handler(
                    servicer.StartHeadControl,
                    request_deserializer=voice__server__pb2.StartHeadControlRequest.FromString,
                    response_serializer=voice__server__pb2.StartHeadControlReply.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'voice_server.VoiceServerService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class VoiceServerService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def SetText(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/voice_server.VoiceServerService/SetText',
            voice__server__pb2.SetTextRequest.SerializeToString,
            voice__server__pb2.SetTextReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SetStyleBertVitsParam(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/voice_server.VoiceServerService/SetStyleBertVitsParam',
            voice__server__pb2.SetStyleBertVitsParamRequest.SerializeToString,
            voice__server__pb2.SetStyleBertVitsParamReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SetVoicevoxParam(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/voice_server.VoiceServerService/SetVoicevoxParam',
            voice__server__pb2.SetVoicevoxParamRequest.SerializeToString,
            voice__server__pb2.SetVoicevoxParamReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SetAivisParam(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/voice_server.VoiceServerService/SetAivisParam',
            voice__server__pb2.SetAivisParamRequest.SerializeToString,
            voice__server__pb2.SetAivisParamReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def InterruptVoice(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/voice_server.VoiceServerService/InterruptVoice',
            voice__server__pb2.InterruptVoiceRequest.SerializeToString,
            voice__server__pb2.InterruptVoiceReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def EnableVoicePlay(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/voice_server.VoiceServerService/EnableVoicePlay',
            voice__server__pb2.EnableVoicePlayRequest.SerializeToString,
            voice__server__pb2.EnableVoicePlayReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def DisableVoicePlay(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/voice_server.VoiceServerService/DisableVoicePlay',
            voice__server__pb2.DisableVoicePlayRequest.SerializeToString,
            voice__server__pb2.DisableVoicePlayReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def IsVoicePlaying(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/voice_server.VoiceServerService/IsVoicePlaying',
            voice__server__pb2.IsVoicePlayingRequest.SerializeToString,
            voice__server__pb2.IsVoicePlayingReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SentenceEnd(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/voice_server.VoiceServerService/SentenceEnd',
            voice__server__pb2.SentenceEndRequest.SerializeToString,
            voice__server__pb2.SentenceEndReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def StartHeadControl(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/voice_server.VoiceServerService/StartHeadControl',
            voice__server__pb2.StartHeadControlRequest.SerializeToString,
            voice__server__pb2.StartHeadControlReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
