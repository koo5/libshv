#include "rpcdriver.h"
#include "metatypes.h"
#include "chainpackprotocol.h"
#include "cponprotocol.h"
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
	switch (protocolVersion()) {
	case Cpon:
		shv::core::chainpack::CponProtocol::write(os_packed_data, msg);
		break;
	default:
		shv::core::chainpack::ChainPackProtocol::write(os_packed_data, msg);
		break;
	}
	std::string packed_data = os_packed_data.str();
	logRpc() << "send message: packed data: " << (packed_data.size() > 250? "<... long data ...>" :
				(protocolVersion() == Cpon? packed_data: shv::core::Utils::toHex(packed_data)));

	enqueueDataToSend(Chunk{std::move(packed_data)});
}

void RpcDriver::sendRawData(std::string &&data)
{
	enqueueDataToSend(Chunk{std::move(data)});
}

void RpcDriver::enqueueDataToSend(RpcDriver::Chunk &&chunk_to_enqueue)
{
	/// LOCK_FOR_SEND lock mutex here in the multithreaded environment
	lockSendQueue();
	if(!chunk_to_enqueue.empty())
		m_chunkQueue.push_back(std::move(chunk_to_enqueue));
	if(!isOpen()) {
		shvError() << "write data error, socket is not open!";
		return;
	}
	flush();
	writeQueue();
	/// UNLOCK_FOR_SEND unlock mutex here in the multithreaded environment
	unlockSendQueue();
}

void RpcDriver::writeQueue()
{
	if(m_chunkQueue.empty())
		return;
	logRpc() << "writePendingData(), queue len:" << m_chunkQueue.size();
	//static int hi_cnt = 0;
	const Chunk &chunk = m_chunkQueue[0];

	if(m_topChunkBytesWrittenSoFar == 0) {
		std::string protocol_version_data;
		{
			std::ostringstream os;
			shv::core::chainpack::ChainPackProtocol::writeUIntData(os, protocolVersion());
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
		auto len = writeBytes(chunk.data() + m_topChunkBytesWrittenSoFar, chunk.length() - m_topChunkBytesWrittenSoFar);
		if(len < 0)
			SHV_EXCEPTION("Write socket error!");
		if(len == 0)
			SHV_EXCEPTION("Design error! At least 1 byte of data shall be always written to the socket");

		logRpc() << "writeQueue - data len:" << chunk.length() << "start index:" << m_topChunkBytesWrittenSoFar << "bytes written:" << len << "remaining:" << (chunk.length() - m_topChunkBytesWrittenSoFar - len);
		m_topChunkBytesWrittenSoFar += len;
		if(m_topChunkBytesWrittenSoFar == chunk.length()) {
			m_topChunkBytesWrittenSoFar = 0;
			m_chunkQueue.pop_front();
		}
	}
}

void RpcDriver::onBytesRead(std::string &&bytes)
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

	bool ok;
	uint64_t chunk_len = ChainPackProtocol::readUIntData(in, &ok);
	if(!ok)
		return 0;

	size_t read_len = (size_t)in.tellg() + chunk_len;

	uint64_t protocol_version = ChainPackProtocol::readUIntData(in, &ok);
	if(!ok)
		return 0;

	logRpc() << "\t chunk len:" << chunk_len << "read_len:" << read_len << "stream pos:" << in.tellg();
	if(read_len > read_data.length())
		return 0;

	//		 << "reading bytes:" << (protocolVersion() == Cpon? read_data: shv::core::Utils::toHex(read_data));

	RpcValue msg;
	switch (protocol_version) {
	case Cpon:
		msg = CponProtocol::read(read_data, (size_t)in.tellg());
		break;
	case ChainPack:
		msg = ChainPackProtocol::read(in);
		break;
	default:
		shvError() << "Throwing away message with unknown protocol version:" << protocol_version;
		break;
	}
	onMessageReceived(msg);
	return read_len;
}

void RpcDriver::onMessageReceived(const RpcValue &msg)
{
	logRpc() << "\t message received:" << msg.toCpon();
	//logLongFiles() << "\t emitting message received:" << msg.dumpText();
	if(m_messageReceivedCallback)
		m_messageReceivedCallback(msg);
}

} // namespace chainpack
} // namespace core
} // namespace shv
