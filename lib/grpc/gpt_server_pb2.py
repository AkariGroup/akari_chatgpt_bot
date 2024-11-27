# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: gpt_server.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='gpt_server.proto',
  package='gpt_server',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x10gpt_server.proto\x12\ngpt_server\"C\n\rSetGptRequest\x12\x0c\n\x04text\x18\x01 \x01(\t\x12\x16\n\tis_finish\x18\x02 \x01(\x08H\x00\x88\x01\x01\x42\x0c\n\n_is_finish\"\x1e\n\x0bSetGptReply\x12\x0f\n\x07success\x18\x01 \x01(\x08\"\x15\n\x13InterruptGptRequest\"$\n\x11InterruptGptReply\x12\x0f\n\x07success\x18\x01 \x01(\x08\"\x13\n\x11SendMotionRequest\"\"\n\x0fSendMotionReply\x12\x0f\n\x07success\x18\x01 \x01(\x08\x32\xea\x01\n\x10GptServerService\x12<\n\x06SetGpt\x12\x19.gpt_server.SetGptRequest\x1a\x17.gpt_server.SetGptReply\x12N\n\x0cInterruptGpt\x12\x1f.gpt_server.InterruptGptRequest\x1a\x1d.gpt_server.InterruptGptReply\x12H\n\nSendMotion\x12\x1d.gpt_server.SendMotionRequest\x1a\x1b.gpt_server.SendMotionReplyb\x06proto3'
)




_SETGPTREQUEST = _descriptor.Descriptor(
  name='SetGptRequest',
  full_name='gpt_server.SetGptRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='text', full_name='gpt_server.SetGptRequest.text', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='is_finish', full_name='gpt_server.SetGptRequest.is_finish', index=1,
      number=2, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
    _descriptor.OneofDescriptor(
      name='_is_finish', full_name='gpt_server.SetGptRequest._is_finish',
      index=0, containing_type=None,
      create_key=_descriptor._internal_create_key,
    fields=[]),
  ],
  serialized_start=32,
  serialized_end=99,
)


_SETGPTREPLY = _descriptor.Descriptor(
  name='SetGptReply',
  full_name='gpt_server.SetGptReply',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='success', full_name='gpt_server.SetGptReply.success', index=0,
      number=1, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=101,
  serialized_end=131,
)


_INTERRUPTGPTREQUEST = _descriptor.Descriptor(
  name='InterruptGptRequest',
  full_name='gpt_server.InterruptGptRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=133,
  serialized_end=154,
)


_INTERRUPTGPTREPLY = _descriptor.Descriptor(
  name='InterruptGptReply',
  full_name='gpt_server.InterruptGptReply',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='success', full_name='gpt_server.InterruptGptReply.success', index=0,
      number=1, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=156,
  serialized_end=192,
)


_SENDMOTIONREQUEST = _descriptor.Descriptor(
  name='SendMotionRequest',
  full_name='gpt_server.SendMotionRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=194,
  serialized_end=213,
)


_SENDMOTIONREPLY = _descriptor.Descriptor(
  name='SendMotionReply',
  full_name='gpt_server.SendMotionReply',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='success', full_name='gpt_server.SendMotionReply.success', index=0,
      number=1, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=215,
  serialized_end=249,
)

_SETGPTREQUEST.oneofs_by_name['_is_finish'].fields.append(
  _SETGPTREQUEST.fields_by_name['is_finish'])
_SETGPTREQUEST.fields_by_name['is_finish'].containing_oneof = _SETGPTREQUEST.oneofs_by_name['_is_finish']
DESCRIPTOR.message_types_by_name['SetGptRequest'] = _SETGPTREQUEST
DESCRIPTOR.message_types_by_name['SetGptReply'] = _SETGPTREPLY
DESCRIPTOR.message_types_by_name['InterruptGptRequest'] = _INTERRUPTGPTREQUEST
DESCRIPTOR.message_types_by_name['InterruptGptReply'] = _INTERRUPTGPTREPLY
DESCRIPTOR.message_types_by_name['SendMotionRequest'] = _SENDMOTIONREQUEST
DESCRIPTOR.message_types_by_name['SendMotionReply'] = _SENDMOTIONREPLY
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

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



_GPTSERVERSERVICE = _descriptor.ServiceDescriptor(
  name='GptServerService',
  full_name='gpt_server.GptServerService',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_start=252,
  serialized_end=486,
  methods=[
  _descriptor.MethodDescriptor(
    name='SetGpt',
    full_name='gpt_server.GptServerService.SetGpt',
    index=0,
    containing_service=None,
    input_type=_SETGPTREQUEST,
    output_type=_SETGPTREPLY,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='InterruptGpt',
    full_name='gpt_server.GptServerService.InterruptGpt',
    index=1,
    containing_service=None,
    input_type=_INTERRUPTGPTREQUEST,
    output_type=_INTERRUPTGPTREPLY,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='SendMotion',
    full_name='gpt_server.GptServerService.SendMotion',
    index=2,
    containing_service=None,
    input_type=_SENDMOTIONREQUEST,
    output_type=_SENDMOTIONREPLY,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
])
_sym_db.RegisterServiceDescriptor(_GPTSERVERSERVICE)

DESCRIPTOR.services_by_name['GptServerService'] = _GPTSERVERSERVICE

# @@protoc_insertion_point(module_scope)
