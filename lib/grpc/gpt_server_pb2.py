# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: gpt_server.proto
# Protobuf Python Version: 4.25.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x10gpt_server.proto\x12\ngpt_server\"0\n\rSetGptRequest\x12\x0c\n\x04text\x18\x01 \x01(\t\x12\x11\n\tis_finish\x18\x02 \x01(\x08\"\x1e\n\x0bSetGptReply\x12\x0f\n\x07success\x18\x01 \x01(\x08\"\x15\n\x13InterruptGptRequest\"$\n\x11InterruptGptReply\x12\x0f\n\x07success\x18\x01 \x01(\x08\x32\xa0\x01\n\x10GptServerService\x12<\n\x06SetGpt\x12\x19.gpt_server.SetGptRequest\x1a\x17.gpt_server.SetGptReply\x12N\n\x0cInterruptGpt\x12\x1f.gpt_server.InterruptGptRequest\x1a\x1d.gpt_server.InterruptGptReplyb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'gpt_server_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_SETGPTREQUEST']._serialized_start=32
  _globals['_SETGPTREQUEST']._serialized_end=80
  _globals['_SETGPTREPLY']._serialized_start=82
  _globals['_SETGPTREPLY']._serialized_end=112
  _globals['_INTERRUPTGPTREQUEST']._serialized_start=114
  _globals['_INTERRUPTGPTREQUEST']._serialized_end=135
  _globals['_INTERRUPTGPTREPLY']._serialized_start=137
  _globals['_INTERRUPTGPTREPLY']._serialized_end=173
  _globals['_GPTSERVERSERVICE']._serialized_start=176
  _globals['_GPTSERVERSERVICE']._serialized_end=336
# @@protoc_insertion_point(module_scope)
