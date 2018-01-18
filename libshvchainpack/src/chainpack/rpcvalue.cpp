/* Copyright (c) 2013 Dropbox, Inc.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

#include "rpcvalue.h"
#include "cponprotocol.h"

#include "exception.h"
#include "utils.h"

#include <cassert>
#include <cstdlib>
#include <cstdio>
#include <ctime>
#include <sstream>
#include <iostream>
//#include <utility>

namespace {
#if defined _WIN32 || defined LIBC_NEWLIB
// see http://pubs.opengroup.org/onlinepubs/9699919799/basedefs/V1_chap04.html#tag_04_15
int is_leap(unsigned y)
{
	y += 1900;
	return (y % 4) == 0 && ((y % 100) != 0 || (y % 400) == 0);
}

time_t timegm(struct tm *tm)
{
	static const unsigned ndays[2][12] = {
		{31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31},
		{31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31}
	};
	time_t res = 0;
	int i;

	for (i = 70; i < tm->tm_year; ++i) {
		res += is_leap(i) ? 366 : 365;
	}

	for (i = 0; i < tm->tm_mon; ++i) {
		res += ndays[is_leap(tm->tm_year)][i];
	}
	res += tm->tm_mday - 1;
	res *= 24;
	res += tm->tm_hour;
	res *= 60;
	res += tm->tm_min;
	res *= 60;
	res += tm->tm_sec;
	return res;
}
#endif
} // namespace

namespace shv {
namespace chainpack {

/*
using std::string;
*/
class RpcValue::AbstractValueData
{
public:
	virtual ~AbstractValueData() {}

	virtual RpcValue::Type type() const {return RpcValue::Type::Invalid;}
	virtual RpcValue::Type arrayType() const {return RpcValue::Type::Invalid;}

	virtual const RpcValue::MetaData &metaData() const = 0;
	virtual void setMetaData(RpcValue::MetaData &&meta_data) = 0;
	virtual void setMetaValue(RpcValue::UInt key, const RpcValue &val) = 0;

	virtual bool equals(const AbstractValueData * other) const = 0;
	//virtual bool less(const Data * other) const = 0;

	virtual bool isNull() const {return false;}
	virtual double toDouble() const {return 0;}
	virtual RpcValue::Decimal toDecimal() const { return RpcValue::Decimal{}; }
	virtual RpcValue::Int toInt() const {return 0;}
	virtual RpcValue::UInt toUInt() const {return 0;}
	virtual bool toBool() const {return false;}
	virtual RpcValue::DateTime toDateTime() const { return RpcValue::DateTime{}; }
	virtual const std::string &toString() const;
	virtual const RpcValue::Blob &toBlob() const;
	virtual const RpcValue::List &toList() const;
	virtual const RpcValue::Array &toArray() const;
	virtual const RpcValue::Map &toMap() const;
	virtual const RpcValue::IMap &toIMap() const;
	virtual size_t count() const {return 0;}

	virtual RpcValue at(RpcValue::UInt i) const;
	virtual RpcValue at(const RpcValue::String &key) const;
	virtual void set(RpcValue::UInt ix, const RpcValue &val);
	virtual void set(const RpcValue::String &key, const RpcValue &val);
};

/* * * * * * * * * * * * * * * * * * * *
 * Value wrappers
 */

template <RpcValue::Type tag, typename T>
class ValueData : public RpcValue::AbstractValueData
{
protected:
	explicit ValueData(const T &value) : m_value(value) {}
	explicit ValueData(T &&value) : m_value(std::move(value)) {}
	// disable copy (because of m_metaData)
	ValueData(const ValueData &o) = delete;
	ValueData& operator=(const ValueData &o) = delete;
	//ValueData(ValueData &&o) = delete;
	//ValueData& operator=(ValueData &&o) = delete;
	virtual ~ValueData() override
	{
		if(m_metaData)
			delete m_metaData;
	}

	RpcValue::Type type() const override { return tag; }

	const RpcValue::MetaData &metaData() const
	{
		static RpcValue::MetaData md;
		if(!m_metaData)
			return md;
		return *m_metaData;
	}

	void setMetaData(RpcValue::MetaData &&d)
	{
		if(m_metaData)
			(*m_metaData) = std::move(d);
		else
			m_metaData = new RpcValue::MetaData(std::move(d));
	}

	void setMetaValue(RpcValue::UInt key, const RpcValue &val)
	{
		if(!m_metaData)
			m_metaData = new RpcValue::MetaData();
		m_metaData->setValue(key, val);
	}
protected:
	T m_value;
	RpcValue::MetaData *m_metaData = nullptr;
};

class ChainPackDouble final : public ValueData<RpcValue::Type::Double, double>
{
	double toDouble() const override { return m_value; }
	RpcValue::Int toInt() const override { return static_cast<int>(m_value); }
	bool equals(const RpcValue::AbstractValueData * other) const override { return m_value == other->toDouble(); }
	//bool less(const Data * other) const override { return m_value < other->toDouble(); }
public:
	explicit ChainPackDouble(double value) : ValueData(value) {}
};

class ChainPackDecimal final : public ValueData<RpcValue::Type::Decimal, RpcValue::Decimal>
{
	double toDouble() const override { return m_value.toDouble(); }
	RpcValue::Int toInt() const override { return static_cast<int>(m_value.toDouble()); }
	RpcValue::Decimal toDecimal() const override { return m_value; }
	bool equals(const RpcValue::AbstractValueData * other) const override { return toDouble() == other->toDouble(); }
	//bool less(const Data * other) const override { return m_value < other->toDouble(); }
public:
	explicit ChainPackDecimal(RpcValue::Decimal &&value) : ValueData(std::move(value)) {}
};

class ChainPackInt final : public ValueData<RpcValue::Type::Int, RpcValue::Int>
{
	double toDouble() const override { return m_value; }
	RpcValue::Int toInt() const override { return m_value; }
	RpcValue::UInt toUInt() const override { return (unsigned int)m_value; }
	bool equals(const RpcValue::AbstractValueData * other) const override { return m_value == other->toInt(); }
	//bool less(const Data * other) const override { return m_value < other->toDouble(); }
public:
	explicit ChainPackInt(RpcValue::Int value) : ValueData(value) {}
};

class ChainPackUInt : public ValueData<RpcValue::Type::UInt, RpcValue::UInt>
{
protected:
	double toDouble() const override { return m_value; }
	RpcValue::Int toInt() const override { return m_value; }
	RpcValue::UInt toUInt() const override { return m_value; }
protected:
	bool equals(const RpcValue::AbstractValueData * other) const override { return m_value == other->toUInt(); }
	//bool less(const Data * other) const override { return m_value < other->toDouble(); }
public:
	explicit ChainPackUInt(RpcValue::UInt value) : ValueData(value) {}
};

class ChainPackBoolean final : public ValueData<RpcValue::Type::Bool, bool>
{
	bool toBool() const override { return m_value; }
	RpcValue::Int toInt() const override { return m_value? true: false; }
	RpcValue::UInt toUInt() const override { return toInt(); }
	bool equals(const RpcValue::AbstractValueData * other) const override { return m_value == other->toBool(); }
public:
	explicit ChainPackBoolean(bool value) : ValueData(value) {}
};

class ChainPackDateTime final : public ValueData<RpcValue::Type::DateTime, RpcValue::DateTime>
{
	bool toBool() const override { return m_value.msecsSinceEpoch() != 0; }
	RpcValue::Int toInt() const override { return m_value.msecsSinceEpoch(); }
	RpcValue::UInt toUInt() const override { return m_value.msecsSinceEpoch(); }
	RpcValue::DateTime toDateTime() const override { return m_value; }
	bool equals(const RpcValue::AbstractValueData * other) const override { return m_value.msecsSinceEpoch() == other->toInt(); }
public:
	explicit ChainPackDateTime(RpcValue::DateTime value) : ValueData(value) {}
};

class ChainPackString : public ValueData<RpcValue::Type::String, RpcValue::String>
{
	const std::string &toString() const override { return m_value; }
	bool equals(const RpcValue::AbstractValueData * other) const override { return m_value == other->toString(); }
public:
	explicit ChainPackString(const RpcValue::String &value) : ValueData(value) {}
	explicit ChainPackString(RpcValue::String &&value) : ValueData(std::move(value)) {}
};

class ChainPackBlob final : public ValueData<RpcValue::Type::Blob, RpcValue::Blob>
{
	const RpcValue::Blob &toBlob() const override { return m_value; }
	bool equals(const RpcValue::AbstractValueData * other) const override { return m_value == other->toBlob(); }
public:
	explicit ChainPackBlob(const RpcValue::Blob &value) : ValueData(value) {}
	explicit ChainPackBlob(RpcValue::Blob &&value) : ValueData(std::move(value)) {}
	explicit ChainPackBlob(const uint8_t *bytes, size_t size) : ValueData(RpcValue::Blob()) {
		m_value.reserve(size);
		for (size_t i = 0; i < size; ++i) {
			m_value[i] = bytes[i];
		}
	}
};

class ChainPackList final : public ValueData<RpcValue::Type::List, RpcValue::List>
{
	size_t count() const override {return m_value.size();}
	RpcValue at(RpcValue::UInt i) const override;
	void set(RpcValue::UInt key, const RpcValue &val) override;
	bool equals(const RpcValue::AbstractValueData * other) const override { return m_value == other->toList(); }
public:
	explicit ChainPackList(const RpcValue::List &value) : ValueData(value) {}
	explicit ChainPackList(RpcValue::List &&value) : ValueData(move(value)) {}

	const RpcValue::List &toList() const override { return m_value; }
};

class ChainPackArray final : public ValueData<RpcValue::Type::Array, RpcValue::Array>
{
	size_t count() const override {return m_value.size();}
	RpcValue at(RpcValue::UInt i) const override;
	bool equals(const RpcValue::AbstractValueData * other) const override
	{
		const RpcValue::Array other_array = other->toArray();
		if(m_value.size() != other_array.size())
			return false;
		for (size_t i = 0; i < m_value.size(); ++i) {
			const RpcValue v1 = m_value.valueAt(i);
			const RpcValue v2 = other_array.valueAt(i);
			if(v1 == v2)
				continue;
			return false;
		}
		return true;
	}
	/*
	void checkSameType()
	{
		Value::Type::Enum type = Value::Type::Invalid;
		int n = 0;
		for (const auto &value : m_value) {
			Value::Type::Enum t = value.type();
			if(n++ == 0) {
				type = t;
			}
			else if(t != type) {
				SHV_EXCEPTION("Table must contain values of same type!");
			}
		}
	}
	*/
public:
	explicit ChainPackArray(const RpcValue::Array &value) : ValueData(value) {}
	explicit ChainPackArray(RpcValue::Array &&value) noexcept : ValueData(std::move(value)) {}
	//explicit ChainPackTable(const ChainPack::List &value) : ValueData(value) {}
	//explicit ChainPackTable(ChainPack::List &&value) : ValueData(move(value)) {}

	RpcValue::Type arrayType() const override {return m_value.type();}
	const RpcValue::Array &toArray() const override { return m_value; }
};

class ChainPackMap final : public ValueData<RpcValue::Type::Map, RpcValue::Map>
{
	//const ChainPack::Map &toMap() const override { return m_value; }
	size_t count() const override {return m_value.size();}
	RpcValue at(const RpcValue::String &key) const override;
	bool equals(const RpcValue::AbstractValueData * other) const override { return m_value == other->toMap(); }
public:
	explicit ChainPackMap(const RpcValue::Map &value) : ValueData(value) {}
	explicit ChainPackMap(RpcValue::Map &&value) : ValueData(move(value)) {}

	const RpcValue::Map &toMap() const override { return m_value; }
};

class ChainPackIMap final : public ValueData<RpcValue::Type::IMap, RpcValue::IMap>
{
	//const ChainPack::Map &toMap() const override { return m_value; }
	size_t count() const override {return m_value.size();}
	RpcValue at(RpcValue::UInt key) const override;
	void set(RpcValue::UInt key, const RpcValue &val) override;
	bool equals(const RpcValue::AbstractValueData * other) const override { return m_value == other->toIMap(); }
public:
	explicit ChainPackIMap(const RpcValue::IMap &value) : ValueData(value) {}
	explicit ChainPackIMap(RpcValue::IMap &&value) : ValueData(std::move(value)) {}

	const RpcValue::IMap &toIMap() const override { return m_value; }
};

class ChainPackNull final : public ValueData<RpcValue::Type::Null, std::nullptr_t>
{
	bool isNull() const override {return true;}
	bool equals(const RpcValue::AbstractValueData * other) const override { return other->isNull(); }
public:
	ChainPackNull() : ValueData({}) {}
};

/* * * * * * * * * * * * * * * * * * * *
 * Static globals - static-init-safe
 */
struct Statics
{
	const std::shared_ptr<RpcValue::AbstractValueData> null = std::make_shared<ChainPackNull>();
	const std::shared_ptr<RpcValue::AbstractValueData> t = std::make_shared<ChainPackBoolean>(true);
	const std::shared_ptr<RpcValue::AbstractValueData> f = std::make_shared<ChainPackBoolean>(false);
	const RpcValue::String empty_string;
	const RpcValue::Blob empty_blob;
	//const std::vector<ChainPack> empty_vector;
	//const std::map<ChainPack::String, ChainPack> empty_map;
	Statics() {}
};

static const Statics & statics()
{
	static const Statics s {};
	return s;
}

static const RpcValue::String & static_empty_string() { return statics().empty_string; }
static const RpcValue::Blob & static_empty_blob() { return statics().empty_blob; }

static const RpcValue & static_chain_pack_invalid() { static const RpcValue s{}; return s; }
//static const ChainPack & static_chain_pack_null() { static const ChainPack s{statics().null}; return s; }
static const RpcValue::List & static_empty_list() { static const RpcValue::List s{}; return s; }
static const RpcValue::Array & static_empty_array() { static const RpcValue::Array s{}; return s; }
static const RpcValue::Map & static_empty_map() { static const RpcValue::Map s{}; return s; }
static const RpcValue::IMap & static_empty_imap() { static const RpcValue::IMap s{}; return s; }

/* * * * * * * * * * * * * * * * * * * *
 * Constructors
 */

RpcValue::RpcValue() noexcept {}
RpcValue::RpcValue(std::nullptr_t) noexcept : m_ptr(statics().null) {}
RpcValue::RpcValue(double value) : m_ptr(std::make_shared<ChainPackDouble>(value)) {}
RpcValue::RpcValue(RpcValue::Decimal value) : m_ptr(std::make_shared<ChainPackDecimal>(std::move(value))) {}
RpcValue::RpcValue(Int value) : m_ptr(std::make_shared<ChainPackInt>(value)) {}
RpcValue::RpcValue(UInt value) : m_ptr(std::make_shared<ChainPackUInt>(value)) {}
RpcValue::RpcValue(bool value) : m_ptr(value ? statics().t : statics().f) {}
RpcValue::RpcValue(const RpcValue::DateTime &value) : m_ptr(std::make_shared<ChainPackDateTime>(value)) {}

RpcValue::RpcValue(const RpcValue::Blob &value) : m_ptr(std::make_shared<ChainPackBlob>(value)) {}
RpcValue::RpcValue(RpcValue::Blob &&value) : m_ptr(std::make_shared<ChainPackBlob>(std::move(value))) {}
RpcValue::RpcValue(const uint8_t * value, size_t size) : m_ptr(std::make_shared<ChainPackBlob>(value, size)) {}
RpcValue::RpcValue(const std::string &value) : m_ptr(std::make_shared<ChainPackString>(value)) {}
RpcValue::RpcValue(std::string &&value) : m_ptr(std::make_shared<ChainPackString>(std::move(value))) {}
RpcValue::RpcValue(const char * value) : m_ptr(std::make_shared<ChainPackString>(value)) {}
RpcValue::RpcValue(const RpcValue::List &values) : m_ptr(std::make_shared<ChainPackList>(values)) {}
RpcValue::RpcValue(RpcValue::List &&values) : m_ptr(std::make_shared<ChainPackList>(std::move(values))) {}

RpcValue::RpcValue(const Array &values) : m_ptr(std::make_shared<ChainPackArray>(values)) {}
RpcValue::RpcValue(RpcValue::Array &&values) : m_ptr(std::make_shared<ChainPackArray>(std::move(values))) {}

RpcValue::RpcValue(const RpcValue::Map &values) : m_ptr(std::make_shared<ChainPackMap>(values)) {}
RpcValue::RpcValue(RpcValue::Map &&values) : m_ptr(std::make_shared<ChainPackMap>(std::move(values))) {}

RpcValue::RpcValue(const RpcValue::IMap &values) : m_ptr(std::make_shared<ChainPackIMap>(values)) {}
RpcValue::RpcValue(RpcValue::IMap &&values) : m_ptr(std::make_shared<ChainPackIMap>(std::move(values))) {}

RpcValue::~RpcValue()
{
	//std::cerr << __FUNCTION__ << " >>>>>>>>>>>>> " << m_ptr.get() << " ref cnt: " << m_ptr.use_count() << " val: " << toStdString() << std::endl;
}
#ifdef RPCVALUE_COPY_AND_SWAP
void RpcValue::swap(RpcValue& other) noexcept
{
	/*
	std::cerr << __FUNCTION__ << " xxxxxxxxxx "
			  << m_ptr.get() << " ref cnt: " << m_ptr.use_count() << " val: " << toStdString()
			  << " X "
			  << other.m_ptr.get() << " ref cnt: " << other.m_ptr.use_count() << " val: " << other.toStdString()
			  << std::endl;
	*/
	std::swap(m_ptr, other.m_ptr);
}
#endif
//Value::Value(const Value::MetaTypeId &value) : m_ptr(std::make_shared<ChainPackMetaTypeId>(value)) {}
//Value::Value(const Value::MetaTypeNameSpaceId &value) : m_ptr(std::make_shared<ChainPackMetaTypeNameSpaceId>(value)) {}
//Value::Value(const Value::MetaTypeName &value) : m_ptr(std::make_shared<ChainPackMetaTypeName>(value)) {}
//Value::Value(const Value::MetaTypeNameSpaceName &value) : m_ptr(std::make_shared<ChainPackMetaTypeNameSpaceName>(value)) {}

/* * * * * * * * * * * * * * * * * * * *
 * Accessors
 */

RpcValue::Type RpcValue::type() const
{
	return m_ptr? m_ptr->type(): Type::Invalid;
}

RpcValue::Type RpcValue::arrayType() const
{
	return m_ptr? m_ptr->arrayType(): Type::Invalid;
}

const RpcValue::MetaData &RpcValue::metaData() const
{
	static MetaData md;
	if(m_ptr)
		return m_ptr->metaData();
	return md;
}

RpcValue RpcValue::metaValue(RpcValue::UInt key) const
{
	const MetaData &md = metaData();
	RpcValue ret = md.value(key);
	return ret;
}

void RpcValue::setMetaData(RpcValue::MetaData &&meta_data)
{
	if(!m_ptr && !meta_data.isEmpty())
		SHVCHP_EXCEPTION("Cannot set valid meta data to invalid ChainPack value!");
	if(m_ptr)
		m_ptr->setMetaData(std::move(meta_data));
}

void RpcValue::setMetaValue(RpcValue::UInt key, const RpcValue &val)
{
	if(!m_ptr && val.isValid())
		SHVCHP_EXCEPTION("Cannot set valid meta value to invalid ChainPack value!");
	if(m_ptr)
		m_ptr->setMetaValue(key, val);
}

bool RpcValue::isValid() const
{
	return !!m_ptr;
}

double RpcValue::toDouble() const { return m_ptr? m_ptr->toDouble(): 0; }
RpcValue::Decimal RpcValue::toDecimal() const { return m_ptr? m_ptr->toDecimal(): Decimal(); }
RpcValue::Int RpcValue::toInt() const { return m_ptr? m_ptr->toInt(): 0; }
RpcValue::UInt RpcValue::toUInt() const { return m_ptr? m_ptr->toUInt(): 0; }
bool RpcValue::toBool() const { return m_ptr? m_ptr->toBool(): false; }
RpcValue::DateTime RpcValue::toDateTime() const { return m_ptr? m_ptr->toDateTime(): RpcValue::DateTime{}; }

const std::string & RpcValue::toString() const { return m_ptr? m_ptr->toString(): static_empty_string(); }
const RpcValue::Blob &RpcValue::toBlob() const { return m_ptr? m_ptr->toBlob(): static_empty_blob(); }

size_t RpcValue::count() const { return m_ptr? m_ptr->count(): 0; }
const RpcValue::List & RpcValue::toList() const { return m_ptr? m_ptr->toList(): static_empty_list(); }
const RpcValue::Array & RpcValue::toArray() const { return m_ptr? m_ptr->toArray(): static_empty_array(); }
const RpcValue::Map & RpcValue::toMap() const { return m_ptr? m_ptr->toMap(): static_empty_map(); }
const RpcValue::IMap &RpcValue::toIMap() const { return m_ptr? m_ptr->toIMap(): static_empty_imap(); }
RpcValue RpcValue::at (RpcValue::UInt i) const { return m_ptr? m_ptr->at(i): RpcValue(); }
RpcValue RpcValue::at (const RpcValue::String &key) const { return m_ptr? m_ptr->at(key): RpcValue(); }

void RpcValue::set(RpcValue::UInt ix, const RpcValue &val)
{
	if(m_ptr)
		m_ptr->set(ix, val);
	else
		std::cerr << __FILE__ << ':' << __LINE__ << " Cannot set value to invalid ChainPack value! Index: " << ix << std::endl;
}

void RpcValue::set(const RpcValue::String &key, const RpcValue &val)
{
	if(m_ptr)
		m_ptr->set(key, val);
	else
		std::cerr << __FILE__ << ':' << __LINE__ << " Cannot set value to invalid ChainPack value! Key: " << key << std::endl;
}

std::string RpcValue::toStdString() const
{
	std::ostringstream out;
	CponProtocol::write(out, *this, CponProtocol::WriteOptions().translateIds(true));
	return out.str();
}

std::string RpcValue::toCpon() const
{
	std::ostringstream out;
	CponProtocol::write(out, *this);
	return out.str();
}

const std::string & RpcValue::AbstractValueData::toString() const { return static_empty_string(); }
const RpcValue::Blob & RpcValue::AbstractValueData::toBlob() const { return static_empty_blob(); }
const RpcValue::List & RpcValue::AbstractValueData::toList() const { return static_empty_list(); }
const RpcValue::Array &RpcValue::AbstractValueData::toArray() const { return static_empty_array(); }
const RpcValue::Map & RpcValue::AbstractValueData::toMap() const { return static_empty_map(); }
const RpcValue::IMap & RpcValue::AbstractValueData::toIMap() const { return static_empty_imap(); }

RpcValue RpcValue::AbstractValueData::at(RpcValue::UInt) const { return RpcValue(); }
RpcValue RpcValue::AbstractValueData::at(const RpcValue::String &) const { return RpcValue(); }

void RpcValue::AbstractValueData::set(RpcValue::UInt ix, const RpcValue &)
{
	std::cerr << __FILE__ << ':' << __LINE__ << " Value::AbstractValueData::set: trivial implementation called! Key: " << ix << std::endl;
}

void RpcValue::AbstractValueData::set(const RpcValue::String &key, const RpcValue &)
{
	std::cerr << __FILE__ << ':' << __LINE__ << " Value::AbstractValueData::set: trivial implementation called! Key: " << key << std::endl;
}


RpcValue ChainPackList::at(RpcValue::UInt i) const
{
	if (i >= m_value.size())
		return static_chain_pack_invalid();
	else
		return m_value[i];
}

void ChainPackList::set(RpcValue::UInt key, const RpcValue &val)
{
	if(key >= m_value.size())
		m_value.resize(key + 1);
	m_value[key] = val;
}

RpcValue ChainPackArray::at(RpcValue::UInt i) const
{
	if (i >= m_value.size())
		return static_chain_pack_invalid();
	else
		return m_value.valueAt(i);
}

/* * * * * * * * * * * * * * * * * * * *
 * Comparison
 */
bool RpcValue::operator== (const RpcValue &other) const
{
	if(isValid() && other.isValid()) {
		if (m_ptr->type() != other.m_ptr->type())
			return false;
		return m_ptr->equals(other.m_ptr.get());
	}
	return (!isValid() && !other.isValid());
}
/*
bool ChainPack::operator< (const ChainPack &other) const
{
	if(isValid() && other.isValid()) {
		if (m_ptr->type() != other.m_ptr->type())
			return m_ptr->type() < other.m_ptr->type();
		return m_ptr->less(other.m_ptr.get());
	}
	return (!isValid() && other.isValid());
}
*/

RpcValue RpcValue::parseCpon(const std::string &in, std::string *err)
{
	if(err) {
		try {
			return CponProtocol::read(in);
		}
		catch(CponProtocol::ParseException &e) {
			*err = e.mesage();
		}
		return RpcValue();
	}
	else {
		return CponProtocol::read(in);
	}
}

const char *RpcValue::typeToName(RpcValue::Type t)
{
	switch (t) {
	case Type::Invalid: return "INVALID";
	case Type::Null: return "Null";
	case Type::UInt: return "UInt";
	case Type::Int: return "Int";
	case Type::Double: return "Double";
	case Type::Bool: return "Bool";
	case Type::Blob: return "Blob";
	case Type::String: return "String";
	case Type::List: return "List";
	case Type::Array: return "Array";
	case Type::Map: return "Map";
	case Type::IMap: return "IMap";
	case Type::DateTime: return "DateTime";
	case Type::MetaIMap: return "MetaIMap";
	case Type::Decimal: return "Decimal";
	}
	return "UNKNOWN"; // just to remove mingw warning
}

RpcValue ChainPackMap::at(const RpcValue::String &key) const
{
	auto iter = m_value.find(key);
	return (iter == m_value.end()) ? static_chain_pack_invalid() : iter->second;
}

RpcValue ChainPackIMap::at(RpcValue::UInt key) const
{
	auto iter = m_value.find(key);
	return (iter == m_value.end()) ? static_chain_pack_invalid() : iter->second;
}

void ChainPackIMap::set(RpcValue::UInt key, const RpcValue &val)
{
	if(val.isValid())
		m_value[key] = val;
	else
		m_value.erase(key);
}

RpcValue::DateTime RpcValue::DateTime::fromString(const std::string &local_date_time_str)
{
	std::istringstream iss(local_date_time_str);
	unsigned int day = 0, month = 0, year = 0, hour = 0, min = 0, sec = 0, msec = 0;
	char dsep, tsep, msep;

	DateTime ret;
	ret.m_msecs = 0;

	if (iss >> year >> dsep >> month >> dsep >> day >> tsep >> hour >> tsep >> min >> tsep >> sec >> msep >> msec) {
		std::tm tm;
		tm.tm_year = year - 1900;
		tm.tm_mon = month - 1;
		tm.tm_mday = day;
		tm.tm_hour = hour;
		tm.tm_min = min;
		tm.tm_sec = sec;
		tm.tm_isdst = -1;
		std::time_t tim = std::mktime(&tm);
		if(tim == -1) {
			std::cerr << "Invalid date time string: " << local_date_time_str;
		}
		else {
			ret.m_msecs = tim * 1000 + msec;
		}
	}
	return ret;
}

RpcValue::DateTime RpcValue::DateTime::fromUtcString(const std::string &utc_date_time_str)
{
	std::istringstream iss(utc_date_time_str);
	unsigned int day = 0, month = 0, year = 0, hour = 0, min = 0, sec = 0, msec = 0;
	char dsep, tsep, msep;

	DateTime ret;
	ret.m_msecs = 0;

	if (iss >> year >> dsep >> month >> dsep >> day >> tsep >> hour >> tsep >> min >> tsep >> sec >> msep >> msec) {
		std::tm tm;
		tm.tm_year = year - 1900;
		tm.tm_mon = month - 1;
		tm.tm_mday = day;
		tm.tm_hour = hour;
		tm.tm_min = min;
		tm.tm_sec = sec;
		tm.tm_isdst = 0;
		std::time_t tim = timegm(&tm);
		if(tim == -1) {
			std::cerr << "Invalid date time string: " << utc_date_time_str;
		}
		else {
			ret.m_msecs = tim * 1000 + msec;
		}
	}
	return ret;
}

RpcValue::DateTime RpcValue::DateTime::fromMSecsSinceEpoch(int64_t msecs)
{
	DateTime ret;
	ret.m_msecs = msecs;
	return ret;
}

std::string RpcValue::DateTime::toString() const
{
	std::time_t tim = m_msecs / 1000;
	std::tm *tm = std::localtime(&tim);
	if(tm == nullptr) {
		std::cerr << "Invalid date time: " << m_msecs;
	}
	else {
		char buffer[80];
		std::strftime(buffer, sizeof(buffer),"%Y-%m-%dT%H:%M:%S",tm);
		std::string ret(buffer);
		ret += '.' + Utils::toString(m_msecs % 1000);
		return ret;
	}
	return std::string();
}

std::string RpcValue::DateTime::toUtcString() const
{
	std::time_t tim = m_msecs / 1000;
	std::tm *tm = std::gmtime(&tim);
	if(tm == nullptr) {
		std::cerr << "Invalid date time: " << m_msecs;
	}
	else {
		char buffer[80];
		std::strftime(buffer, sizeof(buffer),"%Y-%m-%dT%H:%M:%S",tm);
		std::string ret(buffer);
		ret += '.' + Utils::toString(m_msecs % 1000);
		return ret;
	}
	return std::string();
}

std::vector<RpcValue::UInt> RpcValue::MetaData::ikeys() const
{
	std::vector<RpcValue::UInt> ret;
	for(const auto &it : m_imap)
		ret.push_back(it.first);
	return ret;
}

RpcValue RpcValue::MetaData::value(RpcValue::UInt key) const
{
	auto it = m_imap.find(key);
	if(it != m_imap.end())
		return it->second;
	return RpcValue();
}

void RpcValue::MetaData::setValue(RpcValue::UInt key, const RpcValue &val)
{
	if(val.isValid())
		m_imap[key] = val;
	else
		m_imap.erase(key);
}

bool RpcValue::MetaData::operator==(const RpcValue::MetaData &o) const
{
	/*
	std::cerr << "this" << std::endl;
	for(const auto &it : m_imap)
		std::cerr << '\t' << it.first << ": " << it.second.dumpText() << std::endl;
	std::cerr << "other" << std::endl;
	for(const auto &it : o.m_imap)
		std::cerr << '\t' << it.first << ": " << it.second.dumpText() << std::endl;
	*/
	return m_imap == o.m_imap;
}

std::string RpcValue::Decimal::toString() const
{
	std::string ret = Utils::toString(mantisa());
	int prec = precision();
	if(prec >= 0) {
		int len = (int)ret.length();
		if(prec > len)
			ret.insert(0, prec - len, '0'); // insert '0' after dec point
		ret.insert(ret.length() - prec, 1, '.');
		if(prec >= len)
			ret.insert(0, 1, '0'); // insert '0' before dec point
	}
	else {
		ret.insert(ret.length(), -prec, '0');
		ret.push_back('.');
	}
	return ret;
}

}}
