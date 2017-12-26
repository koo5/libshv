import attr
import struct
from datetime import datetime
import enum
import typing, types
import logging_config
import logging
from copy import deepcopy
from math import floor

debug = logging.debug
ARRAY_FLAG_MASK = 64


class ChainpackException(Exception):
	pass

class ChainpackTypeException(ChainpackException):
	pass

class ChainpackDeserializationException(ChainpackException):
	pass


class MetaData(dict):
	pass


class TypeInfo(enum.IntFlag):
	INVALID = -1
	#/// types
	Null=128
	UInt=129
	Int=130
	Double=131
	Bool=132
	Blob=133
	String=134
	DateTime=135
	List=136
	Map=137
	IMap=138
	MetaIMap=139
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
	#/// auxiliary types used for optimization
	FALSE=253
	TRUE=254
	TERMINATION = 255

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
	Array=143
	Map=144
	IMap=145
	MetaIMap=146


class Tag(enum.IntEnum):
	Invalid = 0
	MetaTypeId = 1
	MetaTypeNameSpaceId = 2
	MetaTypeName = 3
	MetaTypeNameSpaceName = 4
	USER = 8


def typeToTypeInfo(type: Type):
	if type == Type.INVALID:  raise Exception("There is no type info for type Invalid");
	if type == Type.Array:    raise Exception("There is no type info for type Array");
	if type == Type.Null:     return TypeInfo.Null;
	if type == Type.UInt:     return TypeInfo.UInt;
	if type == Type.Int:      return TypeInfo.Int;
	if type == Type.Double:   return TypeInfo.Double;
	if type == Type.Bool:     return TypeInfo.Bool;
	if type == Type.Blob:     return TypeInfo.Blob;
	if type == Type.String:   return TypeInfo.String;
	if type == Type.List:     return TypeInfo.List;
	if type == Type.Map:      return TypeInfo.Map;
	if type == Type.IMap:     return TypeInfo.IMap;
	if type == Type.DateTime: return TypeInfo.DateTime;
	if type == Type.MetaIMap: return TypeInfo.MetaIMap;
	raise Exception("Unknown RpcValue::Type!");

def typeInfoToType(type_info: TypeInfo) -> Type:
	if type_info == TypeInfo.Null:     return Type.Null;
	if type_info == TypeInfo.UInt:     return Type.UInt;
	if type_info == TypeInfo.Int:      return Type.Int;
	if type_info == TypeInfo.Double:   return Type.Double;
	if type_info == TypeInfo.Bool:     return Type.Bool;
	if type_info == TypeInfo.Blob:     return Type.Blob;
	if type_info == TypeInfo.String:   return Type.String;
	if type_info == TypeInfo.DateTime: return Type.DateTime;
	if type_info == TypeInfo.List:     return Type.List;
	if type_info == TypeInfo.Map:      return Type.Map;
	if type_info == TypeInfo.IMap:     return Type.IMap;
	if type_info == TypeInfo.MetaIMap: return Type.MetaIMap;
	raise Exception("There is no Type for TypeInfo %s"%(type_info));

def chainpackTypeFromPythonType(t):
	if t == type(None):  return Type.Null,
	if t == bool:        return Type.Bool,
	if t == int:         return Type.Int, Type.UInt,
	if t == float:       return Type.Double,
	if t == datetime:    return Type.DateTime,
	if t == str:         return Type.String,
	if t == list:        return Type.List, Type.Array
	if t == dict:        return Type.Map, Type.IMap
	raise ChainpackTypeException("failed deducing chainpack type for python type %s"%t)


class RpcValue():
	def __init__(s, value, t = None):
		if type(value) == RpcValue:
			s._value = value._value
			s._type = value._type
			s._metaData = deepcopy(value._metaData)
		else:
			s._metaData = {}
			if type(value) == list:
				s._value = []
				for i in value:
					s._value.append(RpcValue(i))
			elif type(value) == dict:
				s._value = {}
				for k,v in value.items():
					if t == Type.IMap:
						#s._value[RpcValue(k, Type.UInt)] = RpcValue(v)
						s._value[k] = RpcValue(v)
					else:
						s._value[k] = RpcValue(v)
			else:
				s._value = value

			if t == None:
				t = chainpackTypeFromPythonType(type(value))[0]
			s._type = t
		if s._type not in chainpackTypeFromPythonType(type(s._value)):
			raise ChainpackTypeException("python type %s for value %s does not match chainpack type %s" % (type(s._value), s._value, s._type))

	def __eq__(s, x):
		return s.type == x.type and s.value == x.value and s._metaData == x._metaData

	def assertEquals(s, x):
		assert s.type == x.type
		assert s.value == x.value
		assert s._metaData == x._metaData

	def __str__(s):
		out = ""
		if len(s._metaData):
			out += '<' + str(s._metaData) + '>'
		#out += RpcValue::typeToName(type());
		#	out += '(' + s + ')';
		#	break;
		return out + str(s._value)

	def __len__(s):
		return len(s._value)

	@property
	def value(s):
		return s._value

	@property
	def type(s):
		return s._type

	def isValid(s):
		return s._type != Type.INVALID

	def toInt(s) -> int:
		assert s._type in [Type.Int, Type.UInt]
		return s._value

	def toBool(s) -> bool:
		assert s._type in [Type.Bool]
		return s._value

	def setMetaValue(s, tag, value):
		value = RpcValue(value)
		if tag in [Tag.MetaTypeId, Tag.MetaTypeNameSpaceId]:
			if value._type == TypeInfo.Int:
				value = RpcValue(value._value, Type.UInt)
		s._metaData[tag] = value


def optimizedMetaTagType(tag: Tag) -> TypeInfo:
	if tag == Tag.MetaTypeId: return TypeInfo.META_TYPE_ID;
	if tag == Tag.MetaTypeNameSpaceId: return TypeInfo.META_TYPE_NAMESPACE_ID;
	return TypeInfo.INVALID;

def optimizeRpcValueIntoType(pack: RpcValue) -> int:
		if (not pack.isValid()):
			raise ChainpackTypeException("Cannot serialize invalid ChainPack.");
		t = pack._type# type: Type
		if(t == Type.Bool) :
			return [TypeInfo.FALSE, TypeInfo.TRUE][pack.toBool()]
		elif t == Type.UInt:
			n = pack.toInt() # type: int
			if n in range(64):
				return n
		elif t == Type.Int:
			n = pack.toInt()
			if n in range(64):
				return n + 64
		return None

class Blob(bytearray):
	DOUBLE_FMT = '!d'

	def __init__(s, value=None):
		if type(value) == RpcValue:
			s.write(RpcValue(value))
		elif isinstance(value, (bytes, bytearray)):
			super().__init__(value)

	def __str__(s):
		return super().__repr__() + str([bin(x) for x in s])

	def add(s, x: bytearray):
		for i in x:
			s.append(i)

	def get(s):
		return s.pop(0)

	def peek(s):
		return s[0]

	def pop_front(s, size: int):
		for i in range(size):
			s.pop(0)

	def read(s):
		metadata = s.readMetaData();
		t: int = s.get();
		if t < 128:
			if(t & 64) :
				#// tiny Int
				n: int = t & 63;
				ret = RpcValue(n, Type.Int);
			else:
				#// tiny UInt
				n: int = t & 63;
				ret = RpcValue(n, Type.UInt);
		elif t in [TypeInfo.TRUE, TypeInfo.FALSE]:
			ret = RpcValue(t == TypeInfo.TRUE)
		else:
			is_array: bool = t & ARRAY_FLAG_MASK;
			type = t & ~ARRAY_FLAG_MASK;
			ret = s.readData(type, is_array);
		if len(metadata):
			ret._metaData = metadata
		return ret;

	def write(s, value: RpcValue) -> int:
		if(not value.isValid()):
			raise ChainpackTypeException("Cannot serialize invalid ChainPack.");
		x = Blob.pack(value)
		s.add(x)
		return len(x)

	@classmethod
	def pack(cls, value):
		#print("pack:", RpcValue(value))
		assert(value._type != TypeInfo.INVALID)
		out = Blob()
		out.writeMetaData(value._metaData);
		t = optimizeRpcValueIntoType(value)
		if t != None:
			out.append(t)
		else:
			if(value._type == Type.Array):
				t = typeToTypeInfo(pack.arrayType) | ARRAY_FLAG_MASK
			else:
				t = typeToTypeInfo(value._type)
			out.append(t)
			out.writeData(value)
		return out

	"""
	
		for key in md.keys():
			type = optimizedMetaTagType(key)
			if(type != TypeInfo.INVALID):
				assert(type >= 0 and type <= 255)
				s.append(type)
				val = md[key]
				assert(val >= 0 and val <= 255)
				s.write_UIntData(val)
			else:
				imap.value[key] = md[key]
		if len(imap):
	"""

	def readMetaData(s) -> MetaData:
		ret = MetaData()
		while True:
			type_info: int = s.peek();
			if type_info == TypeInfo.MetaIMap:
				s.pop(0)
				for k,v in s.readData_IMap().value.items():
					ret[k] = v
			else:
				break;
		return ret;

	def writeMetaData(s, md: MetaData):
		imap = RpcValue(md, Type.IMap)
		if len(imap):
			s.append(TypeInfo.MetaIMap)
			s.writeData_IMap(imap.value);

#	def readTypeInfo(s) -> (TypeInfo, RpcValue, int):
#		t: int = s.get()
#		meta = None
#		if(t & 128):
#			t = t & ~128;
#			meta = s.read();
#		if(t >= 64):
#			return TypeInfo.UInt, meta, t - 64;
#		else: return t, meta

	def readData(s, t: TypeInfo, is_array: bool) -> RpcValue:
		if(is_array):
			val: list = s.readData_Array(t);
			return RpcValue(val);
		else:
			if   t == TypeInfo.Null:     return RpcValue(None)
			elif t == TypeInfo.UInt:     return RpcValue(s.read_UIntData(), Type.UInt)
			elif t == TypeInfo.Int:      return RpcValue(s.read_IntData())
			elif t == TypeInfo.Double:   return RpcValue(s.read_fmt(s.DOUBLE_FMT))
			elif t == TypeInfo.TRUE:     return RpcValue(True)
			elif t == TypeInfo.FALSE:    return RpcValue(False)
			elif t == TypeInfo.DateTime: return RpcValue(s.read_DateTime())
			elif t == TypeInfo.String:   return RpcValue(s.read_String())
			elif t == TypeInfo.Blob:     return RpcValue(s.read_Blob())
			elif t == TypeInfo.List:     return RpcValue(s.readData_List())
			elif t == TypeInfo.Map:      return RpcValue(s.readData_Map())
			elif t == TypeInfo.IMap:     return RpcValue(s.readData_IMap(), TypeInfo.IMap)
			elif t == TypeInfo.Bool:     return RpcValue(s.get() != b'\0')
			else: raise	ChainpackTypeException("Internal error: attempt to read meta type directly. type: " + str(t) + " " + t.name)

	def writeData(s, val: RpcValue):
		v = val.value
		t = val.type # type: Type
		if   t == Type.Null:    return
		elif t == Type.Bool:     s.append([b'0', b'1'][v])
		elif t == Type.UInt:     s.write_UIntData(v)
		elif t == Type.Int:      s.write_IntData(v)
		elif t == Type.Double:   s.write_fmt(s.DOUBLE_FMT, v)
		elif t == Type.DateTime: s.write_DateTime(v)
		elif t == Type.String:   s.write_String(v)
		elif t == Type.Blob:     s.write_Blob(v)
		elif t == Type.List:     s.writeData_List(v)
		elif t == Type.Array:    s.writeData_List(v)
		elif t == Type.Map:      s.writeData_Map(v)
		elif t == Type.IMap:     s.writeData_IMap(v)
		elif t == Type.INVALID:  raise ChainpackTypeException("Internal error: attempt to write invalid type data")
		elif t == Type.MetaIMap:	raise ChainpackTypeException("Internal error: attempt to write metatype directly")

	def read_fmt(s, fmt):
		size = struct.calcsize(fmt)
		r = struct.unpack(fmt, s[:8])
		s.pop_front(size)
		return r

	def write_fmt(s, fmt, value):
		print(type(value))
		s.add(struct.pack(fmt, value))

	def writeData_List(s, v: list):
		for i in v:
			s.write(i)
		s.append(TypeInfo.TERMINATION)

	def readData_List(s) -> list:
		r = []
		while True:
			i = s.peek()
			if i == TypeInfo.TERMINATION:
				s.pop(0)
				break
			r.append(s.read())
		return r

	def write_Blob(s, b):
		assert type(b) in (bytearray, bytes)
		s.write_UIntData(len(b))
		for i in b:
			s.append(i)

	def read_Blob(s):
		r = bytearray()
		for i in range(s.read_UIntData()):
			r.append(s.read_UIntData())
		return r

	def write_String(s, v):
		b = v.encode('utf-8')
		s.write_Blob(b)

	def read_String(s):
		return s.read_Blob().decode('utf-8')

	def write_DateTime(s, v):
		s.write_IntData(floor(v.timestamp()*1000))

	def read_DateTime(s):
		datetime.utcfromtimestamp(s.read_IntData() / 1000)

	def readData_IMap(s) -> RpcValue:
		ret = RpcValue({}, Type.IMap)
		#map_size: int = s.read_UIntData()
		#for i in range(map_size):
		while True:
			if s.peek() == TypeInfo.TERMINATION:
				s.pop(0)
				break
			key = s.read_UIntData()
			ret.value[key] = s.read()
		return ret

	def writeData_IMap(s, map: dict) -> None:
		assert type(map) == dict
		for k, v in map.items():
			if not isinstance(k, int) or k < 0:
				raise ChainpackTypeException('k.type != Type.UInt')
			s.write_UIntData(k)
			s.write(v)
		s.append(TypeInfo.TERMINATION)

	def readData_Map(s) -> RpcValue:
		ret = RpcValue({}, Type.Map)
		while True:
			if s.peek() == TypeInfo.TERMINATION:
				break
			key = s.read()
			ret.value[key] = s.read()
		return ret

	def writeData_Map(s, map: dict) -> None:
		assert type(map) == dict
		for k, v in map.items():
			s.write(k)
			s.write(v)
		s.append(TypeInfo.TERMINATION)

	"""/* UInt
	   0 ... 127              |0|x|x|x|x|x|x|x|<-- LSB
	  128 ... 16383 (2^14-1)  |1|0|x|x|x|x|x|x| |x|x|x|x|x|x|x|x|<-- LSB
	2^14 ... 2097151 (2^21-1) |1|1|0|x|x|x|x|x| |x|x|x|x|x|x|x|x| |x|x|x|x|x|x|x|x|<-- LSB
	                          |1|1|1|0|x|x|x|x| |x|x|x|x|x|x|x|x| |x|x|x|x|x|x|x|x| |x|x|x|x|x|x|x|x|<-- LSB
	                          |1|1|1|1|n|n|n|n| |x|x|x|x|x|x|x|x| |x|x|x|x|x|x|x|x| |x|x|x|x|x|x|x|x| ... <-- LSB
	                          n ==  0 -> 4 bytes (32 bit number)
	                          n ==  1 -> 5 bytes
	                          n == 14 -> 19 bytes
	                          n == 15 -> for future (number of bytes will be specified in next byte)
	*/"""

	UINT_MASK_CNT = 4

	def read_UIntData(s):
		n = 0;
		masks = (127, 63, 31, 15)
		if (not len(s)):
			raise ChainpackDeserializationException("read_UInt: unexpected end of stream!");
		head:int = s.get();
		if  (head & 128)== 0: l = 1
		elif(head & 64) == 0: l = 2
		elif(head & 32) == 0: l = 3
		elif(head & 16) == 0: l = 4
		else: l = (head & 15) + s.UINT_MASK_CNT + 1;
		l-=1;
		if(l < 4):
			n = head & masks[l];

		for i in range(l):
			if (not len(s)):
				raise ChainpackDeserializationException("read_UInt: unexpected end of stream!");
			r = s.get();
			n = (n << 8) + r;
		return n;

	def write_UIntData(s, n: int):
		UINT_BYTES_MAX = 19;
		out = bytearray()
		prefixes = (0 << 4, 8 << 4, 12 << 4, 14 << 4);
		while True:
			r = n & 255;
			n = n >> 8;
			out.append(r)
			if not n:
				break
		if(len(out) >= UINT_BYTES_MAX):
			raise Exception("write_UIntData: value too big to pack!");
		msb = out[-1];
		byte_cnt = len(out)
		if (((byte_cnt == 1) and (msb >= 128))
		or ((byte_cnt == 2) and (msb >= 64))
		or ((byte_cnt == 3) and (msb >= 32))
		or ((byte_cnt == 4) and (msb >= 16))
		or (byte_cnt > 4)):
			out.append(0)
		if(len(out) > s.UINT_MASK_CNT):
			out[-1] = 0xF0 | (len(out) - s.UINT_MASK_CNT - 1);
		else:
			prefix = prefixes[len(out)-1];
			out[-1] |= prefix;
		out.reverse()
		s.add(out)

	"""
/*
   0 ... 63              |s|0|x|x|x|x|x|x|<-- LSB
  64 ... 2^13-1          |s|1|0|x|x|x|x|x| |x|x|x|x|x|x|x|x|<-- LSB
2^13 ... 2^20-1          |s|1|1|0|x|x|x|x| |x|x|x|x|x|x|x|x| |x|x|x|x|x|x|x|x|<-- LSB
                         |s|1|1|1|n|n|n|n| |x|x|x|x|x|x|x|x| |x|x|x|x|x|x|x|x| |x|x|x|x|x|x|x|x|<-- LSB
                          n ==  0 -> 3 bytes
                          n ==  1 -> 4 bytes
                          n == 14 -> 18 bytes
                          n == 15 -> for future (number of bytes will be specified in next byte)
*/
	"""

	INT_MASK_CNT = 3;

	def read_IntData(s):
		n = 0;
		masks = (63, 31, 15);
		if (not len(s)):
			raise ChainpackDeserializationException("read_Int: unexpected end of stream!");
		head:int = s.get();
		sign :bool = head & 128;

		if  (head & 64) == 0: l = 1
		elif(head & 32) == 0: l = 2
		elif(head & 16) == 0: l = 3
		elif(head & 16) == 0: l = 4
		else: l = (head & 15) + s.INT_MASK_CNT + 1;

		if(l < 4):
			l-=1
			n = head & masks[l];
		else:
			l-=1

		for i in range(l):
			if (not len(s)):
				raise ChainpackDeserializationException("read_Int: unexpected end of stream!");
			r = s.get();
			n = (n << 8) + r;

		if(sign):
			n = -n;
		return n;


	def write_IntData(s, n):
		INT_BYTES_MAX = 18;
		prefixes = (0 << 3, 8 << 3, 12 << 3)
	#if(n == std::numeric_limits<T>::min()) {
	#	std::cerr << "cannot pack MIN_INT, will be packed as MIN_INT+1\n";
	#	n++;
		out = bytearray()
		sign = (n < 0);
		if(sign):
			n = -n;
		while True:
			r = n & 255;
			n = n >> 8;
			out.append(r)
			if not n:
				break
		if (len(out) > INT_BYTES_MAX) or ((len(out) == INT_BYTES_MAX) and (r & 128)):
			raise Exception("write_IntData: value too big to pack!");
		msb = out[-1];
		byte_cnt = len(out)
		if (((byte_cnt == 1) and (msb >= 64))
		or ((byte_cnt == 2) and (msb >= 32))
		or ((byte_cnt == 3) and (msb >= 16))
		or (byte_cnt > 3)):
			out.append(0)
		if(byte_cnt > s.INT_MASK_CNT):
			out[-1] = 0x70 | (byte_cnt - s.INT_MASK_CNT - 1);
		else:
			out[-1] |= prefixes[byte_cnt-1];
		if(sign):
			bytes[-1] |= 128;
		out.reverse()
		s.add(out)


	def readData_Array(s, item_type_info):
		#item_type = typeInfoToType(item_type_info)
		ret = RpcValue([], Type.Array)
		size: int = s.read_UIntData()
		for i in range(size):
			ret.value.append(readData(item_type_info, False))

