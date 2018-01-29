import enum
import meta
from value import *

class uint(int):
	pass


class RpcMessage():
	def __init__(s, val: RpcValue = None) -> None:
		if val == None:
			val = RpcValue(None)
		else:
			assert(val.isIMap());
		s._value: RpcValue = val;

	def hasKey(s, key: meta.RpcMessage.Key) -> bool:
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
		if s.isValid() and (meta.RpcMessage.Tag.RequestId in s._value._metaData):
			return s._value._metaData[meta.RpcMessage.Tag.RequestId].toUInt();
		return 0

	def setId(s, id: uint) -> None:
		s.checkMetaValues();
		s.checkRpcTypeMetaValue();
		s.setMetaValue(meta.RpcMessage.Key.Id, RpcValue(id));

	def isValid(s) -> bool:
		return s._value.isValid()

	def isRequest(s) -> bool:
		return s.hasKey(meta.RpcMessage.Key.Method);

	def isNotify(s) -> bool:
		return s.isRequest() and not s.hasKey(meta.RpcMessage.Key.Id);

	def isResponse(s) -> bool:
		return s.rpcType() == hasKey(meta.RpcMessage.RpcCallType.Response)

	def write(out: ChainPackProtocol) -> int:
		assert(s._value.isValid());
		assert(s.rpcType() != meta.RpcMessage.RpcCallType.Undefined);
		return out.write(s._value);

	def rpcType(s) -> meta.RpcMessage.RpcCallType:
		rpc_id: int = s.id();
		has_method: bool = s.hasKey(meta.RpcMessage.Key.Method);
		if(has_method):
			if rpc_id > 0:
				return meta.RpcMessage.RpcCallType.Request
			else:
				return meta.RpcMessage.RpcCallType.Notify;
		if s.hasKey(meta.RpcMessage.Key.Result) or s.hasKey(meta.RpcMessage.Key.Error):
			return meta.RpcMessage.RpcCallType.Response;
		return meta.RpcMessage.RpcCallType.Undefined;

	def checkMetaValues(s) -> None:
		if not s._value.isValid():
			s._value = RpcValue({}, Type.IMap)
			s._value.setMetaValue(meta.Tag.MetaTypeId, meta.RpcMessageID);

	def checkRpcTypeMetaValue(s):
		if s.isResponse():
			rpc_type = meta.RpcMessage.RpcCallType.Response
		elif s.isNotify():
			rpc_type = meta.RpcMessage.RpcCallType.Notify
		else:
			rpc_type = meta.RpcMessage.RpcCallType.Request
		s.setMetaValue(meta.RpcMessage.Tag.RpcCallType, rpc_type);

	def method(s) -> str:
		return value(meta.RpcMessage.Key.Method).toString();

	def setMethod(s, met: str) -> None:
		s.setRpcValue(meta.RpcMessage.Key.Method, RpcValue(met));

	def params(s) -> RpcValue:
		return value(meta.RpcMessage.Key.Params);

	def setParams(s, p: RpcValue) -> None:
		s.setRpcValue(meta.RpcMessage.Key.Params, p);


class RpcRequest(RpcMessage):
	def params(s) -> RpcValue:
		return value(meta.RpcMessage.Key.Params);

	def setParams(s, p: RpcValue):
		s.setValue(meta.RpcMessage.Key.Params, p);


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
			return s.get([Key.Message.toString()], "")

	def error(self) -> Error:
		return Error(value(meta.RpcMessage.Key.Error).toImap());

	def setError(self, err: RpcResponse) -> RpcResponse:
		setRpcValue(Key.Error, RpcValue(err));
		s.checkRpcTypeMetaValue();

	def result(self) -> RpcValue:
		return value(Key.Result);

	def setResult(self, res: RpcValue) -> RpcResponse:
		s.setValue(Key.Result, res);

