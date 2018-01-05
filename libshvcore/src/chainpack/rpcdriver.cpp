#include "rpcdriver.h"
#include "metatypes.h"
#include "chainpackprotocol.h"
#include "../core/shvexception.h"
#include "../core/log.h"

#include <sstream>
#include <iostream>

#define logRpc() shvCDebug("rpc")

namespace shv {
namespace core {
namespace chainpack {

int RpcDriver::s_defaultRpcTimeout = 5000;

RpcDriver::RpcDriver()
{
}

RpcDriver::~RpcDriver()
{
}

void RpcDriver::sendMessage(const shv::core::chainpack::RpcValue &msg)
{
	using namespace std;
	//shvLogFuncFrame() << msg.toStdString();
	std::ostringstream os_packed_data;
	shv::core::chainpack::ChainPackProtocol::write(os_packed_data, msg);
	std::string packed_data = os_packed_data.str();
	logRpc() << "send message: packed data: " << (packed_data.size() > 50? "<... long data ...>" : packed_data);

	enqueueDataToSend(Chunk{std::move(packed_data)});
}

void RpcDriver::enqueueDataToSend(RpcDriver::Chunk &&chunk_to_enqueue)
{
	/// LOCK_FOR_SEND lock mutex here in the multothreaded environment
	if(!chunk_to_enqueue.empty())
		m_chunkQueue.push_back(std::move(chunk_to_enqueue));
	if(!isOpen()) {
		shvError() << "write data error, socket is not open!";
		return;
	}
	flushNoBlock();
	writeQueue();
	/// UNLOCK_FOR_SEND unlock mutex here in the multothreaded environment
}

namespace {
const unsigned PROTOCOL_VERSION = 1;
}

void RpcDriver::writeQueue()
{
	if(m_chunkQueue.empty())
		return;
	logRpc() << "writePendingData(), HI prio queue len:" << m_chunkQueue.size();
	//static int hi_cnt = 0;
	const Chunk &chunk = m_chunkQueue[0];

	if(m_headChunkBytesWrittenSoFar == 0) {
		std::string protocol_version_data;
		{
			std::ostringstream os;
			shv::core::chainpack::ChainPackProtocol::writeUIntData(os, PROTOCOL_VERSION);
			protocol_version_data = os.str();
		}
		{
			std::ostringstream os;
			shv::core::chainpack::ChainPackProtocol::writeUIntData(os, chunk.length() + protocol_version_data.length());
			std::string packet_len_data = os.str();
			auto len = writeBytes(packet_len_data.data(), packet_len_data.length());
			if(len < 0)
				SHV_EXCEPTION("Write socket error!");
			if(len < (int)packet_len_data.length())
				SHV_EXCEPTION("Design error! Chunk length shall be always written at once to the socket");
		}
		{
			auto len = writeBytes(protocol_version_data.data(), protocol_version_data.length());
			if(len < 0)
				SHV_EXCEPTION("Write socket error!");
			if(len != 1)
				SHV_EXCEPTION("Design error! Protocol version shall be always written at once to the socket");
		}
	}

	{
		auto len = writeBytes(chunk.data() + m_headChunkBytesWrittenSoFar, chunk.length() - m_headChunkBytesWrittenSoFar);
		if(len < 0)
			SHV_EXCEPTION("Write socket error!");
		if(len == 0)
			SHV_EXCEPTION("Design error! At least 1 byte of data shall be always written to the socket");

		logRpc() << "writeQueue - data len:" << chunk.length() << "start index:" << m_headChunkBytesWrittenSoFar << "bytes written:" << len << "remaining:" << (chunk.length() - m_headChunkBytesWrittenSoFar - len);
		m_headChunkBytesWrittenSoFar += len;
		if(m_headChunkBytesWrittenSoFar == chunk.length()) {
			m_headChunkBytesWrittenSoFar = 0;
			m_chunkQueue.pop_front();
		}
	}
}

void RpcDriver::bytesRead(std::string &&bytes)
{
	logRpc() << bytes.length() << "bytes of data read";
	m_readData += std::string(std::move(bytes));
	while(true) {
		int len = processReadData(m_readData);
		//shvInfo() << len << "bytes of" << m_readData.size() << "processed";
		if(len > 0)
			m_readData = m_readData.substr(len);
		else
			break;
	}
}

int RpcDriver::processReadData(const std::string &read_data)
{
	logRpc() << __FUNCTION__ << "data len:" << read_data.length();
	using namespace shv::core::chainpack;

	std::istringstream in(read_data);

	uint64_t chunk_len = ChainPackProtocol::readUIntData(in);

	size_t read_len = (size_t)in.tellg() + chunk_len;

	uint64_t protocol_version = ChainPackProtocol::readUIntData(in);

	if(protocol_version != PROTOCOL_VERSION)
		SHV_EXCEPTION("Unsupported protocol version");

	logRpc() << "\t chunk len:" << chunk_len << "read_len:" << read_len << "stream pos:" << in.tellg();
	if(read_len > read_data.length())
		return 0;

	RpcValue msg = ChainPackProtocol::read(in);
	onMessageReceived(msg);
	return read_len;
}

void RpcDriver::onMessageReceived(const RpcValue &msg)
{
	logRpc() << "\t emitting message received:" << msg.toStdString();
	//logLongFiles() << "\t emitting message received:" << msg.dumpText();
	if(m_messageReceivedCallback)
		m_messageReceivedCallback(msg);
}

} // namespace chainpack
} // namespace core
} // namespace shv
