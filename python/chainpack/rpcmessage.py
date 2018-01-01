import enum
import meta
from value import *

class uint(int):
	pass



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

	class Tag(enum.IntFlag):
		RequestId = meta.Tag.USER,
		RpcCallType,
		DeviceId,
		MAX

	class RpcCallType(enum.IntFlag):
		Undefined = 0,
		Request,
		Response,
		Notify

	def __init__(s, val: RpcValue) -> None:
		assert(val.isIMap());
		s._value: RpcValue = val;

	def hasKey(s, key: Key) -> bool:
		assert(s._value.type == Type.IMap)
		return key in s._value

	def value(s, key: uint) -> RpcValue:
		return s.__getitem__(key)

	def setValue(s, key: uint, val: RpcValue):
		assert(key >= meta.RpcMessage.Key.Method and key < meta.RpcMessage.Key.MAX);
		s.checkMetaValues();
		s._value.set(key, val);

	def setMetaValue(s, key: int, val: RpcValue):
		s.checkMetaValues();
		s._value.setMetaValue(key, val);

	def id(s) -> uint:
		return s.__getitem__(Key.Id).toUInt();

	def setId(s, id: uint) -> None:
		s.__setitem__(Key.Id, RpcValue(id));

	def isValid(s) -> bool:
		return ._value.isValid()

	def isRequest(s) -> bool:
		return s.hasKey(Key.Method);

	def isNotify(s) -> bool:
		return s.isRequest() and not s.hasKey(Key.Id);

	def isResponse(s) -> bool:
		return s.hasKey(Key.Id) and (hasKey(Key.Result) or hasKey(Key.Error));

	def write(out: Blob) -> int:
		assert(s._value.isValid());
		assert(rpcType() != meta.RpcMessage.RpcCallType.Undefined);
		return Blob.write(out, s._value);

	def rpcType(s) -> meta.RpcMessage.RpcCallType.Enum:
		rpc_id: int = s.id();
		has_method: bool = s.hasKey(meta.RpcMessage.Key::Method);
		if(has_method)
			if rpc_id > 0:
				return meta.RpcMessage.RpcCallType.Request
				return meta.RpcMessage.RpcCallType.Notify;
		if s.hasKey(meta.RpcMessage.Key.Result) or s.hasKey(meta.RpcMessage.Key.Error):
			return meta.RpcMessage.RpcCallType.Response;
		return meta.RpcMessage.RpcCallType.Undefined;

	def checkMetaValues(s) -> None:
		if(!s._value.isValid()):
			s._value = RpcValue({}, Type.IMap)
			s._value.setMetaValue(Tag.MetaTypeId, meta.RpcMessage.ID);

	def checkRpcTypeMetaValue(s):
		if isResponse():
			rpc_type = meta.RpcMessage.RpcCallType.Response
		elif isNotify():
			rpc_type = meta.RpcMessage.RpcCallType.Notify
		else:
			rpc_type = RpcMessage.RpcCallType.Request
		s.setMetaValue(meta.RpcMessage.Tag.RpcCallType, rpc_type);


	def method(s) -> str:
		return value(Key.Method).toString();

	def setMethod(s, met: str) -> None:
		s.setRpcValue(Key.Method, RpcValue(met));

	def params(s) -> RpcValue:
		return value(Key.Params);

	def setParams(s, p: RpcValue) -> None:
		s.setRpcValue(Key.Params, p);

	#def __getitem__(s, key: uint) -> RpcValue:
	#	return s._value[key]

	#def __setitem__(uint: key, RpcValue: val):
	#	assert type(key) == uint
	#	assert(key >= Key.Id and key < Key.MAX_KEY);
	#	s.ensureMetaRpcValues();
	#	s._value[key] = val



class RpcRequest(RpcMessage):
	RpcValue RpcRequest::params() const
	{
		return value(meta::RpcMessage::Key::Params);
	}

	RpcRequest& RpcRequest::setParams(const RpcValue& p)
	{
		setValue(meta::RpcMessage::Key::Params, p);
		return *this;
	}




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
		return Error(value(meta.RpcResponse.Error).toImap());

	def setError(self, RpcResponse: err) -> RpcResponse
		setRpcValue(Key.Error, RpcValue(err));
		checkRpcTypeMetaValue();

	def result(self) -> RpcValue:
		return value(meta.RpcMessage.Key.Result);

	def setResult(self, res: RpcValue) -> RpcResponse:
		s.setValue(meta.RpcMessage.Key.Result, res);

	RpcResponse::Error::ErrorType RpcResponse::Error::code() const
	{
		auto iter = find(KeyCode);
		return (iter == end()) ? NoError : (ErrorType)(iter->second.toUInt());
	}

	RpcResponse::Error& RpcResponse::Error::setCode(ErrorType c)
	{
		(*this)[KeyCode] = RpcValue{(RpcValue::UInt)c};
		return *this;
	}

	RpcResponse::Error& RpcResponse::Error::setMessage(RpcValue::String &&mess)
	{
		(*this)[KeyMessage] = RpcValue{std::move(mess)};
		return *this;
	}

	RpcValue::String RpcResponse::Error::message() const
	{
		auto iter = find(KeyMessage);
		return (iter == end()) ? RpcValue::String{} : iter->second.toString();
	}

	std::string RpcMessage::toStdString() const
	{
		return m_value.toStdString();
	}


