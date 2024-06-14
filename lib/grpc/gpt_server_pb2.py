# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: gpt_server.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x10gpt_server.proto\x12\ngpt_server\"C\n\rSetGptRequest\x12\x0c\n\x04text\x18\x01 \x01(\t\x12\x16\n\tis_finish\x18\x02 \x01(\x08H\x00\x88\x01\x01\x42\x0c\n\n_is_finish\"\x1e\n\x0bSetGptReply\x12\x0f\n\x07success\x18\x01 \x01(\x08\"\x15\n\x13InterruptGptRequest\"$\n\x11InterruptGptReply\x12\x0f\n\x07success\x18\x01 \x01(\x08\"\x13\n\x11SendMotionRequest\"\"\n\x0fSendMotionReply\x12\x0f\n\x07success\x18\x01 \x01(\x08\x32\xea\x01\n\x10GptServerService\x12<\n\x06SetGpt\x12\x19.gpt_server.SetGptRequest\x1a\x17.gpt_server.SetGptReply\x12N\n\x0cInterruptGpt\x12\x1f.gpt_server.InterruptGptRequest\x1a\x1d.gpt_server.InterruptGptReply\x12H\n\nSendMotion\x12\x1d.gpt_server.SendMotionRequest\x1a\x1b.gpt_server.SendMotionReplyb\x06proto3')



_SETGPTREQUEST = DESCRIPTOR.message_types_by_name['SetGptRequest']
_SETGPTREPLY = DESCRIPTOR.message_types_by_name['SetGptReply']
_INTERRUPTGPTREQUEST = DESCRIPTOR.message_types_by_name['InterruptGptRequest']
_INTERRUPTGPTREPLY = DESCRIPTOR.message_types_by_name['InterruptGptReply']
_SENDMOTIONREQUEST = DESCRIPTOR.message_types_by_name['SendMotionRequest']
_SENDMOTIONREPLY = DESCRIPTOR.message_types_by_name['SendMotionReply']
SetGptRequest = _reflection.GeneratedProtocolMessageType('SetGptRequest', (_message.Message,), {
  'DESCRIPTOR' : _SETGPTREQUEST,
  '__module__' : 'gpt_server_pb2'
  # @@protoc_insertion_point(class_scope:gpt_server.SetGptRequest)
  })
_sym_db.RegisterMessage(SetGptRequest)

SetGptReply = _reflection.GeneratedProtocolMessageType('SetGptReply', (_message.Message,), {
  'DESCRIPTOR' : _SETGPTREPLY,
  '__module__' : 'gpt_server_pb2'
  # @@protoc_insertion_point(class_scope:gpt_server.SetGptReply)
  })
_sym_db.RegisterMessage(SetGptReply)

InterruptGptRequest = _reflection.GeneratedProtocolMessageType('InterruptGptRequest', (_message.Message,), {
  'DESCRIPTOR' : _INTERRUPTGPTREQUEST,
  '__module__' : 'gpt_server_pb2'
  # @@protoc_insertion_point(class_scope:gpt_server.InterruptGptRequest)
  })
_sym_db.RegisterMessage(InterruptGptRequest)

InterruptGptReply = _reflection.GeneratedProtocolMessageType('InterruptGptReply', (_message.Message,), {
  'DESCRIPTOR' : _INTERRUPTGPTREPLY,
  '__module__' : 'gpt_server_pb2'
  # @@protoc_insertion_point(class_scope:gpt_server.InterruptGptReply)
  })
_sym_db.RegisterMessage(InterruptGptReply)

SendMotionRequest = _reflection.GeneratedProtocolMessageType('SendMotionRequest', (_message.Message,), {
  'DESCRIPTOR' : _SENDMOTIONREQUEST,
  '__module__' : 'gpt_server_pb2'
  # @@protoc_insertion_point(class_scope:gpt_server.SendMotionRequest)
  })
_sym_db.RegisterMessage(SendMotionRequest)

SendMotionReply = _reflection.GeneratedProtocolMessageType('SendMotionReply', (_message.Message,), {
  'DESCRIPTOR' : _SENDMOTIONREPLY,
  '__module__' : 'gpt_server_pb2'
  # @@protoc_insertion_point(class_scope:gpt_server.SendMotionReply)
  })
_sym_db.RegisterMessage(SendMotionReply)

_GPTSERVERSERVICE = DESCRIPTOR.services_by_name['GptServerService']
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _SETGPTREQUEST._serialized_start=32
  _SETGPTREQUEST._serialized_end=99
  _SETGPTREPLY._serialized_start=101
  _SETGPTREPLY._serialized_end=131
  _INTERRUPTGPTREQUEST._serialized_start=133
  _INTERRUPTGPTREQUEST._serialized_end=154
  _INTERRUPTGPTREPLY._serialized_start=156
  _INTERRUPTGPTREPLY._serialized_end=192
  _SENDMOTIONREQUEST._serialized_start=194
  _SENDMOTIONREQUEST._serialized_end=213
  _SENDMOTIONREPLY._serialized_start=215
  _SENDMOTIONREPLY._serialized_end=249
  _GPTSERVERSERVICE._serialized_start=252
  _GPTSERVERSERVICE._serialized_end=486
# @@protoc_insertion_point(module_scope)
