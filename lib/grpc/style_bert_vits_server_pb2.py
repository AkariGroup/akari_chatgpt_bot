# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: style_bert_vits_server.proto
# Protobuf Python Version: 4.25.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1cstyle_bert_vits_server.proto\x12\x16style_bert_vits_server\"\x1e\n\x0eSetTextRequest\x12\x0c\n\x04text\x18\x01 \x01(\t\"\x1f\n\x0cSetTextReply\x12\x0f\n\x07success\x18\x01 \x01(\x08\"\xc7\x01\n\x0fSetParamRequest\x12\x17\n\nmodel_name\x18\x01 \x01(\tH\x00\x88\x01\x01\x12\x15\n\x08model_id\x18\x02 \x01(\x05H\x01\x88\x01\x01\x12\x13\n\x06length\x18\x03 \x01(\x02H\x02\x88\x01\x01\x12\x12\n\x05style\x18\x04 \x01(\tH\x03\x88\x01\x01\x12\x19\n\x0cstyle_weight\x18\x05 \x01(\tH\x04\x88\x01\x01\x42\r\n\x0b_model_nameB\x0b\n\t_model_idB\t\n\x07_lengthB\x08\n\x06_styleB\x0f\n\r_style_weight\" \n\rSetParamReply\x12\x0f\n\x07success\x18\x01 \x01(\x08\"\x17\n\x15InterruptVoiceRequest\"&\n\x13InterruptVoiceReply\x12\x0f\n\x07success\x18\x01 \x01(\x08\"%\n\x16SetVoicePlayFlgRequest\x12\x0b\n\x03\x66lg\x18\x01 \x01(\x08\"\'\n\x14SetVoicePlayFlgReply\x12\x0f\n\x07success\x18\x01 \x01(\x08\x32\xb0\x03\n\x1aStyleBertVitsServerService\x12W\n\x07SetText\x12&.style_bert_vits_server.SetTextRequest\x1a$.style_bert_vits_server.SetTextReply\x12Z\n\x08SetParam\x12\'.style_bert_vits_server.SetParamRequest\x1a%.style_bert_vits_server.SetParamReply\x12l\n\x0eInterruptVoice\x12-.style_bert_vits_server.InterruptVoiceRequest\x1a+.style_bert_vits_server.InterruptVoiceReply\x12o\n\x0fSetVoicePlayFlg\x12..style_bert_vits_server.SetVoicePlayFlgRequest\x1a,.style_bert_vits_server.SetVoicePlayFlgReplyb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'style_bert_vits_server_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_SETTEXTREQUEST']._serialized_start=56
  _globals['_SETTEXTREQUEST']._serialized_end=86
  _globals['_SETTEXTREPLY']._serialized_start=88
  _globals['_SETTEXTREPLY']._serialized_end=119
  _globals['_SETPARAMREQUEST']._serialized_start=122
  _globals['_SETPARAMREQUEST']._serialized_end=321
  _globals['_SETPARAMREPLY']._serialized_start=323
  _globals['_SETPARAMREPLY']._serialized_end=355
  _globals['_INTERRUPTVOICEREQUEST']._serialized_start=357
  _globals['_INTERRUPTVOICEREQUEST']._serialized_end=380
  _globals['_INTERRUPTVOICEREPLY']._serialized_start=382
  _globals['_INTERRUPTVOICEREPLY']._serialized_end=420
  _globals['_SETVOICEPLAYFLGREQUEST']._serialized_start=422
  _globals['_SETVOICEPLAYFLGREQUEST']._serialized_end=459
  _globals['_SETVOICEPLAYFLGREPLY']._serialized_start=461
  _globals['_SETVOICEPLAYFLGREPLY']._serialized_end=500
  _globals['_STYLEBERTVITSSERVERSERVICE']._serialized_start=503
  _globals['_STYLEBERTVITSSERVERSERVICE']._serialized_end=935
# @@protoc_insertion_point(module_scope)
