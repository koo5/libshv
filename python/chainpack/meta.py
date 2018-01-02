import enum

class Tag(enum.IntFlag):
	Invalid = -1,
	MetaTypeId = 1,
	MetaTypeNameSpaceId = 2,
	USER = 8
