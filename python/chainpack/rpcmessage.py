import enum
import meta
from value import *

class uint(int):
	pass


class RpcMessage():

	class Key(enum.IntFlag):
		Id = 1,
		Method = 2,
		Params = 3,
		Result = 4,
		Error = 5,
		ErrorCode = 6,
		ErrorMessage = 7,
		MAX_KEY = 8

	class Tag(enum.IntFlag):
		RequestId = meta.Tag.USER,
		RpcCallType = meta.Tag.USER + 1,
		DeviceId = meta.Tag.USER + 2,
		MAX = meta.Tag.USER + 3

	class RpcCallType(enum.IntFlag):
		Undefined = 0,
		Request = 1,
		Response = 2,
		Notify = 3

	def __init__(s, val: RpcValue) -> None:
		assert(val.isIMap());
		s._value: RpcValue = val;

	def hasKey(s, key: Key) -> bool:
		assert(s._value.type == Type.IMap)
		return key in s._value

	def value(s, key: uint) -> RpcValue:
		return s.__getitem__(key)

	def setValue(s, key: uint, val: RpcValue):
		assert(key >= Key.Method and key < Key.MAX);
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
		return s._value.isValid()

	def isRequest(s) -> bool:
		return s.hasKey(Key.Method);

	def isNotify(s) -> bool:
		return s.isRequest() and not s.hasKey(Key.Id);

	def isResponse(s) -> bool:
		return s.hasKey(Key.Id) and (hasKey(Key.Result) or hasKey(Key.Error));

	def write(out: ChainPackProtocol) -> int:
		assert(s._value.isValid());
		assert(rpcType() != RpcCallType.Undefined);
		return out.write(s._value);

	def rpcType(s) -> RpcCallType:
		rpc_id: int = s.id();
		has_method: bool = s.hasKey(Key.Method);
		if(has_method):
			if rpc_id > 0:
				return RpcCallType.Request
			else:
				return RpcCallType.Notify;
		if s.hasKey(Key.Result) or s.hasKey(Key.Error):
			return RpcCallType.Response;
		return RpcCallType.Undefined;

	def checkMetaValues(s) -> None:
		if not s._value.isValid():
			s._value = RpcValue({}, Type.IMap)
			s._value.setMetaValue(Tag.MetaTypeId, meta.RpcMessageID);

	def checkRpcTypeMetaValue(s):
		if s.isResponse():
			rpc_type = RpcCallType.Response
		elif s.isNotify():
			rpc_type = RpcCallType.Notify
		else:
			rpc_type = RpcMessage.RpcCallType.Request
		s.setMetaValue(Tag.RpcCallType, rpc_type);

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
	def params(s) -> RpcValue:
		return value(Key.Params);

	def setParams(s, p: RpcValue):
		s.setValue(Key.Params, p);

class RpcResponse:
	pass
class RpcResponse(RpcMessage):

	class Key(enum.IntFlag):
		Code = 1,
		KeyMessage = 2

	class ErrorType(enum.IntFlag):
		NoError = 0,
		InvalidRequest = 1,
		MethodNotFound = 2,
		InvalidParams = 3,
		InternalError = 4,
		ParseError = 5,
		SyncMethodCallTimeout = 6,
		SyncMethodCallCancelled = 7,
		MethodInvocationException = 8,
		Unknown = 9

	class Error(dict):

		class Key(enum.IntFlag):
			Code = 1,
			Message = 2

		class ErrorType(enum.IntFlag):
			NoError = 0,
			InvalidRequest = 1,	#// The JSON sent is not a valid Request object.
			MethodNotFound = 2,
			InvalidParams = 3,
			InternalError = 4,
			ParseError = 5,
			SyncMethodCallTimeout = 5,
			SyncMethodCallCancelled = 6,
			MethodInvocationException = 7,
			Unknown = 8

		def code(s) -> ErrorType:
			if Key.Code in s:
				return s[Key.Code].toUInt();
			return ErrorType.NoError

		def setCode(s, c: ErrorType):
			s[KeyCode] = RpcValue(uint(c));
			return s;

		def setMessage(s, msg: str):
			s[KeyMessage] = RpcValue(msg);
			return s

		def message(s) -> str:
			return s.get([Key.KeyMessage.toString()], "")

	def error(self) -> Error:
		return Error(value(meta.RpcResponse.Error).toImap());

	def setError(self, err: RpcResponse) -> RpcResponse:
		setRpcValue(Key.Error, RpcValue(err));
		s.checkRpcTypeMetaValue();

	def result(self) -> RpcValue:
		return value(Key.Result);

	def setResult(self, res: RpcValue) -> RpcResponse:
		s.setValue(Key.Result, res);

