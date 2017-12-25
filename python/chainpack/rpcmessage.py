import enum

from value import *

uint = int

class RpcMessage():
	class Key(enum.IntFlag):
		Id = 1,
		Method,
		Params,
		Result,
		Error,
		ErrorCode,
		ErrorMessage,
		MAX_KEY

	def __init__(self, val: RpcValue) -> None:
		assert(val.isIMap());
		s._value: RpcValue = val;

#	def hasKey(s, key: Key) -> bool:
#		assert(m_value.type == Type.IMap)
#		return key in m_value

#	def value(self, uint: Key) -> RpcValue:
#		return __getitem__(key)
#
#	def __getitem__(self, uint: Key) -> RpcValue:
#		return m_value[key]
#
#	def setRpcValue(self, key: Mey, RpcValue: value) -> None:
#		__setitem__(key, value)

	def __setitem__(uint: key, RpcValue: val):
		assert type(key) == uint
		assert(key >= Key.Id and key < Key.MAX_KEY);
		ensureMetaRpcValues();
		m_value[key] = val


	def id(s) -> uint:
		return s.__getitem__(Key.Id).toUInt();

	def setId(s, uint: id) -> None:
		s.__setitem__(Key::Id, RpcValue(id));

	def isRequest(s) -> bool:
		return s.hasKey(Key.Method);

# bool RpcMessage::isNotify() const
# {
# 	return isRequest() && !hasKey(Key::Id);
# }
#
# bool RpcMessage::isResponse() const
# {
# 	return hasKey(Key::Id) && (hasKey(Key::Result) || hasKey(Key::Error));
# }


	def ensureMetaRpcValues() -> None:
		if(!m_value.isValid()):
			m_value = RpcValue({}, Type.IMap)
			m_value.setMetaValue(Tag.MetaTypeId, GlobalMetaTypeId.ChainPackRpcMessage);
			#/// not needed, Global is default name space
			#//m_value.setMetaValue(RpcValue::Tag::MetaTypeNameSpaceId, MetaTypeNameSpaceId::Global);

	def method() -> str:
		return value(Key.Method).toString();

	def setMethod(self, str: met) -> RpcMessage:
		setRpcValue(Key.Method, RpcValue(met));
		return self;

	def params(self) -> None
		return value(Key.Params);

	def setParams(self, RpcValue: p) -> RpcMessage:
		setRpcValue(Key.Params, p);
		return self;




class RpcResponse(RpcMessage):
	class Error(dict):
		class Key(enum.IntFlag):
			KeyCode = 1,
			KeyMessage
		class ErrorType(enum.IntFlag):
			NoError = 0,
			InvalidRequest,	#// The JSON sent is not a valid Request object.
			MethodNotFound,	#// The method does not exist / is not available.
			InvalidParams,	#// Invalid method parameter(s).
			InternalError,	#// Internal JSON-RPC error.
			ParseError,		#// Invalid JSON was received by the server. An error occurred on the server while parsing the JSON text.
			SyncMethodCallTimeout,
			SyncMethodCallCancelled,
			MethodInvocationException,
			Unknown
		def code(self) -> ErrorType:
			if KeyCode in self:
				return self[KeyCode].toUInt();
			return NoError
		def setCode(self, ErrorType: c) -> Error:
			self[KeyCode] = RpcValue(uint(c));
			return self;

		def setMessage(self, str: mess) -> Error:
			self[KeyMessage] = RpcValue(mess);
			return self

		def message(self) -> str:
			return self.get([Key.KeyMessage.toString()], "")

	def error(self) -> Error:
		return Error(value(Key::Error).toDict());

	def setError(self, RpcResponse: err) -> RpcResponse
		setRpcValue(Key.Error, RpcValue(err));
		return self

	def result(self) -> RpcValue:
		return value(Key.Result);

	def setResult(self, RpcValue: res) -> RpcResponse:
		setRpcValue(Key.Result, res);
		return self






