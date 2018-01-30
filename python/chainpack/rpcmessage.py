import enum
import meta
from value import *


class RpcMessage():
	def __init__(s, val: RpcValue = None) -> None:
		if val == None:
			val = RpcValue(invalid_value, Type.INVALID)
		else:
			assert(val.isIMap());
		s._value: RpcValue = val;

	def hasKey(s, key: meta.RpcMessage.Key) -> bool:
		if s._value.type == Type.IMap:
			return key in s._value.toPython()
		else:
			return False

	def value(s, key: uint) -> RpcValue:
		return s._value._value[key]

	def setValue(s, key: uint, val: RpcValue):
		assert(key >= meta.RpcMessage.Key.Method and key < meta.RpcMessage.Key.MAX);
		s.checkMetaValues();
		s._value._value[key] = val

	def setMetaValue(s, key: int, val: RpcValue):
		s.checkMetaValues();
		s._value.setMetaValue(key, val);

	def id(s) -> uint:
		if s.isValid() and (meta.RpcMessage.Tag.RequestId in s._value._metaData):
			return s._value._metaData[meta.RpcMessage.Tag.RequestId].toUInt();
		return 0

	def setId(s, id: (uint, int)) -> None:
		s.checkMetaValues();
		s.checkRpcTypeMetaValue();
		s.setMetaValue(meta.RpcMessage.Tag.RequestId, RpcValue(uint(id)));

	def isValid(s) -> bool:
		return s._value.isValid()

	def isRequest(s) -> bool:
		return s.rpcType() == meta.RpcMessage.RpcCallType.Request

	def isNotify(s) -> bool:
		return s.rpcType() == meta.RpcMessage.RpcCallType.Notify

	def isResponse(s) -> bool:
		return s.rpcType() == meta.RpcMessage.RpcCallType.Response

	def write(s, out: ChainPackProtocol) -> int:
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
			s._value.setMetaValue(meta.Tag.MetaTypeId, meta.RpcMessage.ID);

	def checkRpcTypeMetaValue(s):
		if s.isResponse():
			rpc_type = meta.RpcMessage.RpcCallType.Response
		elif s.isNotify():
			rpc_type = meta.RpcMessage.RpcCallType.Notify
		else:
			rpc_type = meta.RpcMessage.RpcCallType.Request
		s.setMetaValue(meta.RpcMessage.Tag.RpcCallType, rpc_type);

	def method(s) -> str:
		return s.value(meta.RpcMessage.Key.Method).toString();

	def setMethod(s, met: str) -> None:
		s.setValue(meta.RpcMessage.Key.Method, RpcValue(met));

	def params(s) -> RpcValue:
		return value(meta.RpcMessage.Key.Params);

	def setParams(s, p: RpcValue) -> None:
		s.setRpcValue(meta.RpcMessage.Key.Params, p);


class RpcRequest(RpcMessage):
	def params(s) -> RpcValue:
		return s.value(meta.RpcMessage.Key.Params);

	def setParams(s, p: RpcValue):
		s.setValue(meta.RpcMessage.Key.Params, RpcValue(p));


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
			InvalidRequest = 1,
			MethodNotFound = 2,
			InvalidParams = 3,
			InternalError = 4,
			ParseError = 5,
			SyncMethodCallTimeout = 5,
			SyncMethodCallCancelled = 6,
			MethodInvocationException = 7,
			Unknown = 8

		@classmethod
		def createError(cls, code, message):
			r = cls()
			r.setCode(code)
			r.setMessage(message)
			return r

		def code(s) -> ErrorType:
			if Key.Code in s:
				return s[Key.Code].toUInt();
			return ErrorType.NoError

		def setCode(s, c: ErrorType):
			s[s.__class__.Key.Code] = RpcValue(uint(c));
			return s;

		def setMessage(s, msg: str):
			s[s.__class__.Key.Message] = RpcValue(msg);
			return s

		def message(s) -> str:
			return s.get([Key.Message.toString()], "")

	def error(s) -> Error:
		return RpcResponse.Error(s.value(meta.RpcMessage.Key.Error).toPython());

	def setError(s, err):
		s.setValue(meta.RpcMessage.Key.Error, RpcValue(err, Type.IMap));
		s.checkRpcTypeMetaValue();

	def result(s) -> RpcValue:
		return s.value(meta.RpcMessage.Key.Result);

	def setResult(s, res: RpcValue) -> RpcResponse:
		s.setValue(meta.RpcMessage.Key.Result, RpcValue(res));
		s.checkRpcTypeMetaValue();

