import enum

class Tag(enum.IntFlag):
	Invalid = -1,
	MetaTypeId = 1,
	MetaTypeNameSpaceId = 2,
	USER = 8

RpcMessageID = 1


class RpcMessage():

	class Key(enum.IntFlag):
		Method = 2,
		Params = 3,
		Result = 4,
		Error = 5,
		ErrorCode = 6,
		ErrorMessage = 7,
		MAX = 8

	class Tag(enum.IntFlag):
		RequestId = Tag.USER,
		RpcCallType = Tag.USER + 1,
		DeviceId = Tag.USER + 2,
		MAX = Tag.USER + 3

	class RpcCallType(enum.IntFlag):
		Undefined = 0,
		Request = 1,
		Response = 2,
		Notify = 3
