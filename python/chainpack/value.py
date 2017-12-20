import attr
import struct
from datetime import datetime
import enum
import typing, types
import logging_config
import logging
from copy import deepcopy

debug = logging.debug
ARRAY_FLAG_MASK = 64

class ChainpackTypeException(Exception):
	pass

class MetaData(dict):
	pass

class TypeInfo(enum.IntFlag):
	INVALID = -1
	#/// auxiliary types used for optimization
	TERM = 128 #// first byte of packed Int or UInt cannot be like 0b1000000
	META_TYPE_ID=129
	META_TYPE_NAMESPACE_ID=130
	FALSE=131
	TRUE=132
	CHUNK_HEADER=133
	#/// types
	Null=134
	UInt=135
	Int=136
	Double=137
	Bool=138
	Blob=139
	String=140
	DateTime=141
	List=142
	Map=143
	IMap=144
	MetaIMap=145
	#/// arrays
	#// if bit 6 is set, then packed value is an Array of corresponding values
	Null_Array = Null | ARRAY_FLAG_MASK
	UInt_Array = UInt | ARRAY_FLAG_MASK
	Int_Array = Int | ARRAY_FLAG_MASK
	Double_Array = Double | ARRAY_FLAG_MASK
	Bool_Array = Bool | ARRAY_FLAG_MASK
	Blob_Array = Blob | ARRAY_FLAG_MASK
	String_Array = String | ARRAY_FLAG_MASK
	DateTime_Array = DateTime | ARRAY_FLAG_MASK
	List_Array = List | ARRAY_FLAG_MASK
	Map_Array = Map | ARRAY_FLAG_MASK
	IMap_Array = IMap | ARRAY_FLAG_MASK
	MetaIMap_Array = MetaIMap | ARRAY_FLAG_MASK


class Type(enum.IntFlag):
	INVALID = -1
	Null=134
	UInt=135
	Int=136
	Double=137
	Bool=138
	Blob=139
	String=140
	DateTime=141
	List=142
	Map=143
	IMap=144


class Tag(enum.IntEnum):
	Invalid = 0
	MetaTypeId = 1
	MetaTypeNameSpaceId = 2
	MetaTypeName = 3
	MetaTypeNameSpaceName = 4
	USER = 8


#@attr.attributes
class RpcValue():
	#attr.attrib00
	def __init__(s, value, t = None):
		if type(value) == RpcValue:
			s.m_value = value.m_value
			s.m_type = value.m_type
			s.m_metaData = deepcopy(value.m_metaData)
		else:
			s.m_metaData = {}
			s.m_value = value
			if t == None:
				t = chainpackTypeFromPythonType(type(value))[0]
			s.m_type = t
		if s.m_type not in chainpackTypeFromPythonType(type(s.m_value)):
			raise ChainpackTypeException("python type %s for value %s does not match chainpack type %s"%(type(s.m_value), s.m_value, s.m_type))
	def __str__(s):
		out = ""
		if len(s.m_metaData):
			out += '<' + str(s.m_metaData) + '>'
		#out += RpcValue::typeToName(type());
		#	out += '(' + s + ')';
		#	break;
		return out + str(s.m_value)
	def __len__(s):
		return len(s.m_value)
	def setMetaValue(s, tag, value):
		value = RpcValue(value)
		if tag in [Tag.MetaTypeId, Tag.MetaTypeNameSpaceId]:
			if value.m_type == TypeInfo.Int:
				value = RpcValue(value.m_value, TypeInfo.UInt)
		s.m_metaData[tag] = value
	def isValid(s):
		return s.m_type != Type.INVALID
	def toInt(s):
		assert s.m_type in [Type.Int, Type.UInt]
		return s.m_value

def chainpackTypeFromPythonType(t):
		if t == type(None):    return Type.Null,
		elif t == bool:      return Type.Bool,
		elif t == int:         return Type.Int,
		elif t == float:         return Type.Double,
		elif t == datetime:         return Type.DateTime,
		elif t == str:         return Type.String,
		elif t == list:         return Type.List, Type.Array
		elif t == dict:         return Type.Map, Type.IMap
		else:
			raise ChainpackTypeException("failed deducing chainpack type for python type %s"%t)

def optimizedMetaTagType(tag: Tag) -> TypeInfo:
	if tag == Tag.MetaTypeId: return TypeInfo.META_TYPE_ID;
	if tag == Tag.MetaTypeNameSpaceId: return TypeInfo.META_TYPE_NAMESPACE_ID;
	return TypeInfo.INVALID;

def optimizeRpcValueIntoType(pack: RpcValue) -> (bool, TypeInfo):
		if (not pack.isValid()):
			raise ChainpackTypeException("Cannot serialize invalid ChainPack.");
		t = pack.m_type# type: Type
		if(t == Type.Bool) :
			return True, [TypeInfo.FALSE, TypeInfo.TRUE][pack.toBool()]
		elif t == Type.UInt:
			n = pack.toInt() # type: Int
			if n in range(64):
				return n
		elif t == Type.Int:
			n = pack.toInt() # type: Int
			if n in range(64):
				return n + 64
		elif(type == Type.Array):
			t = typeToTypeInfo(pack.arrayType)
			return t | ARRAY_FLAG_MASK

class Blob(bytearray):
	DOUBLE_FMT = '!d'
	INT_FMT = 'l'
	UINT_FMT = 'L'
	if struct.calcsize(INT_FMT) != 8:
		raise Exception('calcsize(INT_FMT) != 8')

	def __init__(s, value=None):
		if value != None:
			s.write(RpcValue(value))
	def __str__(s):
		return super().__repr__() + str([bin(x) for x in s])

	def write(s, value: RpcValue) -> int:
		if(not value.isValid()):
			raise ChainpackTypeException("Cannot serialize invalid ChainPack.");
		x = Blob.pack(value)
		s.append(x)
		return len(x)

	@classmethod
	def pack(cls, value):
		print("pack:", RpcValue(value))
		assert(value.m_type != TypeInfo.INVALID)
		out = Blob()
		out.writeMetaData(value.m_metaData);
		t = optimizeRpcValueIntoType(value)
		if t != None:
			out.append(t)
		else:
			out.append(value.m_type)
			out.writeData(value)

	def writeMetaData(s, md: MetaData):
		imap = RpcValue({}, TypeInfo.IMap)
		for key in md.keys():
			type = optimizedMetaTagType(key)
			if(type != TypeInfo.INVALID):
				assert(type >= 0 and type <= 255)
				s.append(type)
				val = md[key]
				assert(val >= 0 and val <= 255)
				s.write_UIntData(val)
			else:
				imap[key] = md[(key)]
		if len(imap):
			append(TypeInfo.MetaIMap)
			writeData_IMap(imap);

	def writeData(s, val: RpcValue):
		v = val.m_value
		t = val.m_type # type: Type
		if   t == Type.Null:    return
		elif t == Type.Bool:     s.append([b'0', b'1'][v])
		elif t == Type.UInt:     s.write_fmt(UINT_FMT, v)
		elif t == Type.Int:      s.write_fmt(INT_FMT, v)
		elif t == Type.Double:   s.write_fmt(DOUBLE_FMT, v)
		elif t == Type.DateTime: s.write_DateTime(v)
		elif t == Type.String:   s.write_Blob(v)
		elif t == Type.Blob:     s.write_Blob(v)
		elif t == Type.List:     s.writeData_List(v)
		elif t == Type.Array:    s.writeData_Array(v)
		elif t == Type.Map:      s.writeData_Map(v)
		elif t == Type.IMap:     s.writeData_IMap(v)
		elif t == Type.Invalid:  raise ChainpackTypeException("Internal error: attempt to write invalid type data")
		elif t == Type.MetaIMap:	raise ChainpackTypeException("Internal error: attempt to write metatype directly")

	def pop_front(s, size: int):
		for i in range(size):
			s.pop(0)

	def read_UIntData(s):
		return s.read_fmt(FMT_UINT)

	def readData_IMap(s) -> RpcValue:
		ret = RpcValue({}, Type.IMap)
		int: map_size = s.read_UIntData()
		for i in range(map_size):
			key = s.read_UIntData()
			ret[key] = s.read()
		return ret

	def writeData_IMap(RpcValue: map) -> None:
		assert map.type == Type.IMap
		write_fmt(FMT_UINT, len(map))
		for k, v in map.items():
			write_fmt(FMT_UINT, k)
			write(v)

	def read_fmt(s, fmt):
		size = struct.calcsize(fmt)
		r = struct.unpack(fmt, s)
		s.pop_front(size)
		return r

	def write_fmt(fmt, value):
		append(struct.pack(fmt, value))
    #
	# def write_Double(s, d):
    #
	# def read_Double(s) -> Double:
    #
	# def write_Int(s, i):

	def read(s):
		RpcValue: ret;
		dict: metadata = readMetaData(data);
		int: t = data.get();
		if(t < 128) :
			if(t & 64) :
				#// tiny Int
				int: n = t & 63;
				ret = RpcValue(n, Type.Int);
			else:
				#// tiny UInt
				uint: n = t & 63;
				ret = RpcValue(n, Type.UInt);
		elif type in [TypeInfo.TRUE, TypeInfo.FALSE]:
			ret = RpcValue(t == TypeInfo.TRUE)
		else:
			bool: is_array = t & ARRAY_FLAG_MASK;
			type = t & ~ARRAY_FLAG_MASK;
			#//ChainPackProtocol::TypeInfo::Enum value_type = is_array? type: ChainPackProtocol::TypeInfo::INVALID;
			#//ChainPackProtocol::TypeInfo::Enum array_type = is_array? type: ChainPackProtocol::TypeInfo::INVALID;
			ret = readData(type, is_array, data);
		if len(metadata):
			ret.setMetaData(metadata.deepcopy())
		return ret;

	def peek(s):
		return s[0]

	def readMetaData(s) -> dict:
		MetaData: ret;
		while True:
			int: type_info = s.peek();
			if type_info == TypeInfo.META_TYPE_ID:
				s.pop(0)
				uint: u = s.read_UIntData();
				ret[Tag.MetaTypeId] = u
			elif type_info == TypeInfo.META_TYPE_NAMESPACE_ID:
				s.pop(0)
				uint: u = s.read_UIntData();
				ret[Tag.MetaTypeNameSpaceId] = u
			elif type_info == TypeInfo.MetaIMap:
				s.pop(0)
				ret += s.readData_IMap()
			else:
				break;
		return ret;

	def readTypeInfo(s) -> (TypeInfo, RpcValue, int):
		int: t = s.get()[0]
		meta = None
		if(t & 128):
			t = t & ~128;
			meta = s.read();
		if(t >= 64):
			return TypeInfo.UInt, meta, t - 64;
		else: return t, meta

	def readData(s, t: TypeInfo, is_array: bool) -> RpcValue:
		RpcValue: ret;
		if(is_array):
			list: val = s.readData_Array(type);
			ret = RpcValue(val);
		else:
			if   t == TypeInfo.Null:     return RpcValue(None)
			elif t == TypeInfo.UInt:     return RpcValue(s.read_UIntData(data))
			elif t == TypeInfo.Int:      return RpcValue(s.read_IntData(data))
			elif t == TypeInfo.Double:   return RpcValue(s.read_Double(data))
			elif t == TypeInfo.TRUE:     return RpcValue(True)
			elif t == TypeInfo.FALSE:    return RpcValue(False)
			elif t == TypeInfo.DateTime: return RpcValue(s.read_DateTime(data))
			elif t == TypeInfo.String:   return RpcValue(s.read_Blob(data))
			elif t == TypeInfo.Blob:     return RpcValue(s.read_Blob(data))
			elif t == TypeInfo.List:     return RpcValue(s.readData_List(data))
			elif t == TypeInfo.Map:      return RpcValue(s.readData_Map(data))
			elif t == TypeInfo.IMap:     return RpcValue(s.readData_IMap(data), TypeInfo.IMap)
			elif t == TypeInfo.Bool:     return RpcValue(s.get() != b'0')
			else: raise	ChainpackTypeException("Internal error: attempt to read meta type directly. type: " + str(t) + " " + t.__name__)



