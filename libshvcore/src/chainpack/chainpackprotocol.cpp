#include "chainpackprotocol.h"

#include "../core/shvexception.h"

#include <iostream>
#include <cassert>
#include <limits>

namespace shv {
namespace core {
namespace chainpack {

namespace {

/* UInt
   0 ... 127              |0|x|x|x|x|x|x|x|<-- LSB
  128 ... 16383 (2^14-1)  |1|0|x|x|x|x|x|x| |x|x|x|x|x|x|x|x|<-- LSB
2^14 ... 2097151 (2^21-1) |1|1|0|x|x|x|x|x| |x|x|x|x|x|x|x|x| |x|x|x|x|x|x|x|x|<-- LSB
                          |1|1|1|0|x|x|x|x| |x|x|x|x|x|x|x|x| |x|x|x|x|x|x|x|x| |x|x|x|x|x|x|x|x|<-- LSB
                          |1|1|1|1|n|n|n|n| |x|x|x|x|x|x|x|x| |x|x|x|x|x|x|x|x| |x|x|x|x|x|x|x|x| ... <-- LSB
                          n ==  0 -> 4 bytes (32 bit number)
                          n ==  1 -> 5 bytes
                          n == 14 -> 19 bytes
                          n == 15 -> for future (number of bytes will be specified in next byte)
*/
constexpr int UINT_MASK_CNT = 4;
template<typename T>
T read_UIntData(std::istream &data, bool *ok = nullptr)
{
	T n = 0;
	constexpr uint8_t masks[UINT_MASK_CNT] = {127, 63, 31, 15};
	if(data.eof()) {
		if(ok) {
			*ok = false;
			return 0;
		}
		SHV_EXCEPTION("read_UInt: unexpected end of stream!");
	}
	uint8_t head = data.get();
	int len;
	if((head & 128) == 0) { len = 1; }
	else if((head & 64) == 0) { len = 2; }
	else if((head & 32) == 0) { len = 3; }
	else if((head & 16) == 0) { len = 4; }
	else { len = (head & 15) + UINT_MASK_CNT + 1; }
	if(len < 5) {
		len--;
		n = head & masks[len];
	}
	else {
		len--;
	}
	for (int i = 0; i < len; ++i) {
		if(data.eof()) {
			if(ok) {
				*ok = false;
				return 0;
			}
			SHV_EXCEPTION("read_UInt: unexpected end of stream!");
		}
		uint8_t r = data.get();
		n = (n << 8) + r;
	};
	if(ok)
		*ok = true;
	return n;
}

template<typename T>
void write_UIntData(std::ostream &out, T n)
{
	constexpr int UINT_BYTES_MAX = 19;
	uint8_t bytes[1 + sizeof(T)];
	constexpr int prefixes[UINT_MASK_CNT] = {0 << 4, 8 << 4, 12 << 4, 14 << 4};
	int byte_cnt = 0;
	do {
		uint8_t r = n & 255;
		n = n >> 8;
		bytes[byte_cnt++] = r;
	} while(n);
	if(byte_cnt >= UINT_BYTES_MAX)
		SHV_EXCEPTION("write_UIntData: value too big to pack!");
	bytes[byte_cnt] = 0;
	uint8_t msb = bytes[byte_cnt-1];
	if(byte_cnt == 1)      { if(msb >= 128) byte_cnt++; }
	else if(byte_cnt == 2) { if(msb >= 64) byte_cnt++; }
	else if(byte_cnt == 3) { if(msb >= 32) byte_cnt++; }
	else if(byte_cnt == 4) { if(msb >= 16) byte_cnt++; }
	else byte_cnt++;
	if(byte_cnt > UINT_MASK_CNT) {
		bytes[byte_cnt-1] = 0xF0 | (byte_cnt - UINT_MASK_CNT - 1);
	}
	else {
		uint8_t prefix = (uint8_t)prefixes[byte_cnt-1];
		bytes[byte_cnt-1] |= prefix;
	}
	for (int i = byte_cnt-1; i >= 0; --i) {
		uint8_t r = bytes[i];
		out << r;
	}
}

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

constexpr int INT_MASK_CNT = 3;
template<typename T>
T read_IntData(std::istream &data)
{
	T n = 0;
	constexpr uint8_t masks[INT_MASK_CNT] = {63, 31, 15};
	if(data.eof())
		SHV_EXCEPTION("read_Int: unexpected end of stream!");
	uint8_t head = data.get();
	bool s = head & 128;
	int len;
	if((head & 64) == 0) { len = 1; }
	else if((head & 32) == 0) { len = 2; }
	else if((head & 16) == 0) { len = 3; }
	else { len = (head & 15) + INT_MASK_CNT + 1; }
	if(len < 4) {
		len--;
		n = head & masks[len];
	}
	else {
		len--;
	}
	for (int i = 0; i < len; ++i) {
		if(data.eof())
			SHV_EXCEPTION("read_Int: unexpected end of stream!");
		uint8_t r = data.get();
		n = (n << 8) + r;
	};
	if(s)
		n = -n;
	return n;
}

template<typename T>
void write_IntData(std::ostream &out, T n)
{
	constexpr int INT_BYTES_MAX = 18;
	uint8_t bytes[1 + sizeof(T)];
	constexpr int prefixes[INT_MASK_CNT] = {0 << 3, 8 << 3, 12 << 3};
	if(n == std::numeric_limits<T>::min()) {
		std::cerr << "cannot pack MIN_INT, will be packed as MIN_INT+1\n";
		n++;
	}
	bool s = (n < 0);
	if(s)
		n = -n;
	int byte_cnt = 0;
	do {
		uint8_t r = n & 255;
		n = n >> 8;
		bytes[byte_cnt++] = r;
	} while(n);
	if(byte_cnt >= INT_BYTES_MAX)
		SHV_EXCEPTION("write_UIntData: value too big to pack!");
	bytes[byte_cnt] = 0;
	uint8_t msb = bytes[byte_cnt-1];
	if(byte_cnt == 1)      { if(msb >= 64) byte_cnt++; }
	else if(byte_cnt == 2) { if(msb >= 32) byte_cnt++; }
	else if(byte_cnt == 3) { if(msb >= 16) byte_cnt++; }
	else byte_cnt++;
	if(byte_cnt > 3) {
		bytes[byte_cnt-1] = 0x70 | (byte_cnt - INT_MASK_CNT - 1);
	}
	else {
		uint8_t prefix = (uint8_t)prefixes[byte_cnt-1];
		bytes[byte_cnt-1] |= prefix;
	}
	if(s)
		bytes[byte_cnt-1] |= 128;
	for (int i = byte_cnt-1; i >= 0; --i) {
		uint8_t r = bytes[i];
		out << r;
	}
}

double read_Double(std::istream &data)
{
	union U {uint64_t n; double d;} u;
	u.n = 0;
	int shift = 0;
	for (size_t i = 0; i < sizeof(u.n); ++i) {
		uint8_t r = data.get();
		uint64_t n1 = r;
		n1 <<= shift;
		shift += 8;
		u.n += n1;
	}
	return u.d;
}

void write_Double(std::ostream &out, double d)
{
	union U {uint64_t n; double d;} u;
	assert(sizeof(u.n) == sizeof(u.d));
	u.d = d;
	for (size_t i = 0; i < sizeof(u.n); ++i) {
		uint8_t r = u.n & 255;
		u.n = u.n >> 8;
		out << r;
	}
}

template<typename T>
void write_Blob(std::ostream &out, const T &blob)
{
	using S = typename T::size_type;
	S l = blob.length();
	write_UIntData<S>(out, l);
	//out.reserve(out.size() + l);
	for (S i = 0; i < l; ++i)
		out << (uint8_t)blob[i];
}

template<typename T>
T read_Blob(std::istream &data)
{
	using S = typename T::size_type;
	unsigned int len = read_UIntData<unsigned int>(data);
	T ret;
	//ret.reserve(len);
	for (S i = 0; i < len; ++i)
		ret += data.get();
	return ret;
}

void write_DateTime(std::ostream &out, const RpcValue::DateTime &dt)
{
	uint64_t msecs = dt.msecs;
	write_IntData(out, msecs);
}

RpcValue::DateTime read_DateTime(std::istream &data)
{
	RpcValue::DateTime dt;
	dt.msecs = read_IntData<decltype(dt.msecs)>(data);
	return dt;
}

} // namespace

ChainPackProtocol::TypeInfo::Enum ChainPackProtocol::typeToTypeInfo(RpcValue::Type type)
{
	switch (type) {
	case RpcValue::Type::Invalid:
		SHV_EXCEPTION("There is no type info for type Invalid");
	case RpcValue::Type::Array:
		SHV_EXCEPTION("There is no type info for type Array");
	case RpcValue::Type::Null: return TypeInfo::Null;
	case RpcValue::Type::UInt: return TypeInfo::UInt;
	case RpcValue::Type::Int: return TypeInfo::Int;
	case RpcValue::Type::Double: return TypeInfo::Double;
	case RpcValue::Type::Bool: return TypeInfo::Bool;
	case RpcValue::Type::Blob: return TypeInfo::Blob;
	case RpcValue::Type::String: return TypeInfo::String;
	case RpcValue::Type::List: return TypeInfo::List;
	case RpcValue::Type::Map: return TypeInfo::Map;
	case RpcValue::Type::IMap: return TypeInfo::IMap;
	case RpcValue::Type::DateTime: return TypeInfo::DateTime;
	case RpcValue::Type::MetaIMap: return TypeInfo::MetaIMap;
	}
	SHV_EXCEPTION("Unknown RpcValue::Type!");
	return TypeInfo::INVALID; // just to remove mingw warning
}

RpcValue::Type ChainPackProtocol::typeInfoToType(ChainPackProtocol::TypeInfo::Enum type_info)
{
	switch (type_info) {
	case ChainPackProtocol::TypeInfo::Null: return RpcValue::Type::Null;
	case ChainPackProtocol::TypeInfo::UInt: return RpcValue::Type::UInt;
	case ChainPackProtocol::TypeInfo::Int: return RpcValue::Type::Int;
	case ChainPackProtocol::TypeInfo::Double: return RpcValue::Type::Double;
	case ChainPackProtocol::TypeInfo::Bool: return RpcValue::Type::Bool;
	case ChainPackProtocol::TypeInfo::Blob: return RpcValue::Type::Blob;
	case ChainPackProtocol::TypeInfo::String: return RpcValue::Type::String;
	case ChainPackProtocol::TypeInfo::DateTime: return RpcValue::Type::DateTime;
	case ChainPackProtocol::TypeInfo::List: return RpcValue::Type::List;
	case ChainPackProtocol::TypeInfo::Map: return RpcValue::Type::Map;
	case ChainPackProtocol::TypeInfo::IMap: return RpcValue::Type::IMap;
	case ChainPackProtocol::TypeInfo::MetaIMap: return RpcValue::Type::MetaIMap;
	default:
		SHV_EXCEPTION(std::string("There is type for type info ") + ChainPackProtocol::TypeInfo::name(type_info));
	}
}

const char *ChainPackProtocol::TypeInfo::name(ChainPackProtocol::TypeInfo::Enum e)
{
	switch (e) {
	//case META_TYPE_ID: return "META_TYPE_ID";
	//case META_TYPE_NAMESPACE_ID: return "META_TYPE_NAMESPACE_ID";
	case FALSE: return "FALSE";
	case TRUE: return "TRUE";

	case Null: return "Null";
	case UInt: return "UInt";
	case Int: return "Int";
	case Double: return "Double";
	case Bool: return "Bool";
	case Blob: return "Blob";
	case String: return "String";
	case List: return "List";
	case Map: return "Map";
	case IMap: return "IMap";
	case DateTime: return "DateTime";
	case MetaIMap: return "MetaIMap";

	case Null_Array: return "Null_Array";
	case UInt_Array: return "UInt_Array";
	case Int_Array: return "Int_Array";
	case Double_Array: return "Double_Array";
	case Bool_Array: return "Bool_Array";
	case Blob_Array: return "Blob_Array";
	case String_Array: return "String_Array";
	case DateTime_Array: return "DateTime_Array";
	case List_Array: return "List_Array";
	case Map_Array: return "Map_Array";
	case IMap_Array: return "IMap_Array";
	case MetaIMap_Array: return "MetaIMap_Array";

	case TERM: return "TERM";
	default:
		return "UNKNOWN";
	}
}

void ChainPackProtocol::writeData_Array(std::ostream &out, const RpcValue::Array &array)
{
	unsigned size = array.size();
	write_UIntData(out, size);
	for (unsigned i = 0; i < size; ++i) {
		const RpcValue &cp = array.valueAt(i);
		writeData(out, cp);
	}
}

RpcValue::Array ChainPackProtocol::readData_Array(ChainPackProtocol::TypeInfo::Enum array_type_info, std::istream &data)
{
	RpcValue::Type type = typeInfoToType(array_type_info);
	RpcValue::Array ret(type);
	RpcValue::UInt size = read_UIntData<RpcValue::UInt>(data);
	ret.reserve(size);
	for (unsigned i = 0; i < size; ++i) {
		RpcValue cp = readData(array_type_info, false, data);
		ret.push_back(RpcValue::Array::makeElement(cp));
	}
	return ret;
}

void ChainPackProtocol::writeData_List(std::ostream &out, const RpcValue::List &list)
{
	unsigned size = list.size();
	//write_UIntData(out, size);
	for (unsigned i = 0; i < size; ++i) {
		const RpcValue &cp = list.at(i);
		write(out, cp);
	}
	out << (uint8_t)TypeInfo::TERM;
}

RpcValue::List ChainPackProtocol::readData_List(std::istream &data)
{
	RpcValue::List lst;
	while(true) {
		int b = data.peek();
		if(b == ChainPackProtocol::TypeInfo::TERM) {
			data.get();
			break;
		}
		RpcValue cp = read(data);
		lst.push_back(cp);
	}
	return lst;
}

void ChainPackProtocol::writeData_Map(std::ostream &out, const RpcValue::Map &map)
{
	//unsigned size = map.size();
	//write_UIntData(out, size);
	for (const auto &kv : map) {
		write_Blob<RpcValue::String>(out, kv.first);
		write(out, kv.second);
	}
	out << (uint8_t)TypeInfo::TERM;
}

RpcValue::Map ChainPackProtocol::readData_Map(std::istream &data)
{
	RpcValue::Map ret;
	while(true) {
		int b = data.peek();
		if(b == ChainPackProtocol::TypeInfo::TERM) {
			data.get();
			break;
		}
		RpcValue::String key = read_Blob<RpcValue::String>(data);
		RpcValue cp = read(data);
		ret[key] = cp;
	}
	return ret;
}

void ChainPackProtocol::writeData_IMap(std::ostream &out, const RpcValue::IMap &map)
{
	//unsigned size = map.size();
	//write_UIntData(out, size);
	for (const auto &kv : map) {
		RpcValue::UInt key = kv.first;
		write_UIntData(out, key);
		write(out, kv.second);
	}
	out << (uint8_t)TypeInfo::TERM;
}

RpcValue::IMap ChainPackProtocol::readData_IMap(std::istream &data)
{
	RpcValue::IMap ret;
	while(true) {
		int b = data.peek();
		if(b == ChainPackProtocol::TypeInfo::TERM) {
			data.get();
			break;
		}
		RpcValue::UInt key = read_UIntData<RpcValue::UInt>(data);
		RpcValue cp = read(data);
		ret[key] = cp;
	}
	return ret;
}

int ChainPackProtocol::write(std::ostream &out, const RpcValue &pack)
{
	if(!pack.isValid())
		SHV_EXCEPTION("Cannot serialize invalid ChainPack.");
	std::ostream::pos_type len = out.tellp();
	writeMetaData(out, pack);
	if(!writeTypeInfo(out, pack))
		writeData(out, pack);
	return (out.tellp() - len);
}

void ChainPackProtocol::writeMetaData(std::ostream &out, const RpcValue &pack)
{
	const RpcValue::MetaData &md = pack.metaData();
	if(!md.isEmpty()) {
		const RpcValue::IMap &cim = md.toIMap();
		out << (uint8_t)ChainPackProtocol::TypeInfo::MetaIMap;
		writeData_IMap(out, cim);
	}
}

bool ChainPackProtocol::writeTypeInfo(std::ostream &out, const RpcValue &pack)
{
	if(!pack.isValid())
		SHV_EXCEPTION("Cannot serialize invalid ChainPack.");
	bool ret = false;
	RpcValue::Type type = pack.type();
	int t = TypeInfo::INVALID;
	if(type == RpcValue::Type::Bool) {
		t = pack.toBool()? ChainPackProtocol::TypeInfo::TRUE: ChainPackProtocol::TypeInfo::FALSE;
		ret = true;
	}
	else if(type == RpcValue::Type::UInt) {
		auto n = pack.toUInt();
		if(n < 64) {
			/// TinyUInt
			t = n;
			ret = true;
		}
	}
	else if(type == RpcValue::Type::Int) {
		auto n = pack.toInt();
		if(n >= 0 && n < 64) {
			/// TinyInt
			t = 64 + n;
			ret = true;
		}
	}
	else if(type == RpcValue::Type::Array) {
		t = typeToTypeInfo(pack.arrayType());
		t |= ARRAY_FLAG_MASK;
	}
	if(t == TypeInfo::INVALID) {
		t = typeToTypeInfo(pack.type());
	}
	out << (uint8_t)t;
	return ret;
}

void ChainPackProtocol::writeData(std::ostream &out, const RpcValue &pack)
{
	RpcValue::Type type = pack.type();
	switch (type) {
	case RpcValue::Type::Null: break;
	case RpcValue::Type::Bool: out << (uint8_t)(pack.toBool() ? 1 : 0); break;
	case RpcValue::Type::UInt: { auto u = pack.toUInt(); write_UIntData(out, u); break; }
	case RpcValue::Type::Int: { RpcValue::Int n = pack.toInt(); write_IntData(out, n); break; }
	case RpcValue::Type::Double: write_Double(out, pack.toDouble()); break;
	case RpcValue::Type::DateTime: write_DateTime(out, pack.toDateTime()); break;
	case RpcValue::Type::String: write_Blob(out, pack.toString()); break;
	case RpcValue::Type::Blob: write_Blob(out, pack.toBlob()); break;
	case RpcValue::Type::List: writeData_List(out, pack.toList()); break;
	case RpcValue::Type::Array: writeData_Array(out, pack.toArray()); break;
	case RpcValue::Type::Map: writeData_Map(out, pack.toMap()); break;
	case RpcValue::Type::IMap: writeData_IMap(out, pack.toIMap()); break;
	case RpcValue::Type::Invalid:
	case RpcValue::Type::MetaIMap:
		SHV_EXCEPTION("Internal error: attempt to write helper type directly. type: " + std::string(RpcValue::typeToName(type)));
	}
}

uint64_t ChainPackProtocol::readUIntData(std::istream &data, bool *ok)
{
	bool ok2;
	uint64_t ret = read_UIntData<uint64_t>(data, &ok2);
	if(ok)
		*ok = ok2;
	return ret;
}

void ChainPackProtocol::writeUIntData(std::ostream &out, uint64_t n)
{
	write_UIntData(out, n);
}

RpcValue ChainPackProtocol::read(std::istream &data)
{
	RpcValue ret;
	RpcValue::MetaData meta_data = readMetaData(data);
	uint8_t type = data.get();
	if(type < 128) {
		if(type & 64) {
			// tiny Int
			RpcValue::Int n = type & 63;
			ret = RpcValue(n);
		}
		else {
			// tiny UInt
			RpcValue::UInt n = type & 63;
			ret = RpcValue(n);
		}
	}
	else if(type == ChainPackProtocol::TypeInfo::FALSE) {
		ret = RpcValue(false);
	}
	else if(type == ChainPackProtocol::TypeInfo::TRUE) {
		ret = RpcValue(true);
	}
	if(!ret.isValid()) {
		bool is_array = type & ARRAY_FLAG_MASK;
		type = type & ~ARRAY_FLAG_MASK;
		//ChainPackProtocol::TypeInfo::Enum value_type = is_array? type: ChainPackProtocol::TypeInfo::INVALID;
		//ChainPackProtocol::TypeInfo::Enum array_type = is_array? type: ChainPackProtocol::TypeInfo::INVALID;
		ret = readData((ChainPackProtocol::TypeInfo::Enum)type, is_array, data);
	}
	if(!meta_data.isEmpty())
		ret.setMetaData(std::move(meta_data));
	return ret;
}

RpcValue::MetaData ChainPackProtocol::readMetaData(std::istream &data)
{
	RpcValue::MetaData ret;
	while(true) {
		bool has_meta = true;
		uint8_t type_info = data.peek();
		switch(type_info) {
		/*
		case ChainPackProtocol::TypeInfo::META_TYPE_ID:  {
			data.get();
			RpcValue::UInt u = read_UIntData<RpcValue::UInt>(data);
			ret.setMetaTypeId(u);
			break;
		}
		case ChainPackProtocol::TypeInfo::META_TYPE_NAMESPACE_ID:  {
			data.get();
			RpcValue::UInt u = read_UIntData<RpcValue::UInt>(data);
			ret.setMetaTypeNameSpaceId(u);
			break;
		}
		*/
		case ChainPackProtocol::TypeInfo::MetaIMap:  {
			data.get();
			RpcValue::IMap imap = readData_IMap(data);
			for( const auto &it : imap)
				ret.setValue(it.first, it.second);
			break;
		}
		default:
			has_meta = false;
			break;
		}
		if(!has_meta)
			break;
	}
	return ret;
}

ChainPackProtocol::TypeInfo::Enum ChainPackProtocol::readTypeInfo(std::istream &data, RpcValue &meta, int &tiny_uint)
{
	uint8_t t = data.get();
	if(t & 128) {
		t = t & ~128;
		meta = read(data);
	}
	if(t >= 64) {
		/// TinyUInt
		t -= 64;
		tiny_uint = t;
		return ChainPackProtocol::TypeInfo::UInt;
	}
	else {
		ChainPackProtocol::TypeInfo::Enum type = (ChainPackProtocol::TypeInfo::Enum)t;
		return type;
	}
}

RpcValue ChainPackProtocol::readData(ChainPackProtocol::TypeInfo::Enum type, bool is_array, std::istream &data)
{
	RpcValue ret;
	if(is_array) {
		RpcValue::Array val = readData_Array(type, data);
		ret = RpcValue(val);
	}
	else {
		switch (type) {
		case ChainPackProtocol::TypeInfo::Null:
			ret = RpcValue(nullptr);
			break;
		case ChainPackProtocol::TypeInfo::UInt: { RpcValue::UInt u = read_UIntData<RpcValue::UInt>(data); ret = RpcValue(u); break; }
		case ChainPackProtocol::TypeInfo::Int: { RpcValue::Int i = read_IntData<RpcValue::Int>(data); ret = RpcValue(i); break; }
		case ChainPackProtocol::TypeInfo::Double: { double d = read_Double(data); ret = RpcValue(d); break; }
		case ChainPackProtocol::TypeInfo::TRUE: { bool b = true; ret = RpcValue(b); break; }
		case ChainPackProtocol::TypeInfo::FALSE: { bool b = false; ret = RpcValue(b); break; }
		case ChainPackProtocol::TypeInfo::DateTime: { RpcValue::DateTime val = read_DateTime(data); ret = RpcValue(val); break; }
		case ChainPackProtocol::TypeInfo::String: { RpcValue::String val = read_Blob<RpcValue::String>(data); ret = RpcValue(val); break; }
		case ChainPackProtocol::TypeInfo::Blob: { RpcValue::Blob val = read_Blob<RpcValue::Blob>(data); ret = RpcValue(val); break; }
		case ChainPackProtocol::TypeInfo::List: { RpcValue::List val = readData_List(data); ret = RpcValue(val); break; }
		case ChainPackProtocol::TypeInfo::Map: { RpcValue::Map val = readData_Map(data); ret = RpcValue(val); break; }
		case ChainPackProtocol::TypeInfo::IMap: { RpcValue::IMap val = readData_IMap(data); ret = RpcValue(val); break; }
		case ChainPackProtocol::TypeInfo::Bool: { uint8_t t = data.get(); ret = RpcValue(t != 0); break; }
		default:
			SHV_EXCEPTION("Internal error: attempt to read helper type directly. type: " + shv::core::Utils::toString(type) + " " + TypeInfo::name(type));
		}
	}
	return ret;
}


}}}
