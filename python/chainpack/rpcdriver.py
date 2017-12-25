#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from value import *

import logging
logger=logging.getLogger()
logger.setLevel(logging.DEBUG)
from utils import _print
def out(*vargs):
	logger.debug(_print(*vargs))

defaultRpcTimeout = 5000;
Chunk = str

class RpcDriver():
	def sendMessage(msg: RpcValue):
		out = Blob()
		out.write(msg)
		log("send message: packed data: ",  (if packed_data.size() > 50: str(out[:50]) + "<... long data ...>") else out))
		enqueueDataToSend(Chunk{std::move(packed_data)});

	def enqueueDataToSend(chunk_to_enqueue: Chunk):
		if(len(chunk_to_enqueue))
			m_chunkQueue.append(chunk_to_enqueue[:]));
		if(!isOpen()):
			logger.critical("write data error, socket is not open!")
		return
		flushNoBlock();
		writeQueue();

	PROTOCOL_VERSION = 1;


	def writeQueue(s):
		if(!len(s.m_chunkQueue)):
			return;
		log("writePendingData(), HI prio queue len: %s" % len(s.m_chunkQueue))
		#//static int hi_cnt = 0;
		chunk: Chunk = s.m_chunkQueue[0];

		if s.m_headChunkBytesWrittenSoFar == 0:
			protocol_version_data = Blob(RpcValue(PROTOCOL_VERSION, Type.UInt))
			packet_len_data = Blob(RpcValue(len(protocol_version_data) + len(chunk), Type.UInt))
			written_len = writeBytes(packet_len_data, len(packet_len_data));
			if(written_len < 0):
				raise Exception("Write socket error!");
			if written_len < len(packet_len_data):
				raise Exception("Design error! Chunk length shall be always written at once to the socket");
			
			len = writeBytes(protocol_version_data, len(protocol_version_data));
			if(len < 0):
				raise Exception("Write socket error!");
			if(len != 1)
				raise Exception("Design error! Protocol version shall be always written at once to the socket");

		len = writeBytes(chunk + s.m_headChunkBytesWrittenSoFar, len(chunk) - s.m_headChunkBytesWrittenSoFar);
		if(len < 0):
			raise Exception("Write socket error!");
		if(len == 0):
			raise Exception("Design error! At least 1 byte of data shall be always written to the socket");

		log("writeQueue - data len:", len(chunk),  "start index:", s.m_headChunkBytesWrittenSoFar, "bytes written:", len, "remaining:", (len(chunk) - s.m_headChunkBytesWrittenSoFar - len);
		s.m_headChunkBytesWrittenSoFar += len;
		if(s.m_headChunkBytesWrittenSoFar == len(chunk)):
			s.m_headChunkBytesWrittenSoFar = 0;
			s.m_chunkQueue.pop_front();

	def bytesRead(s, b: bytes):
		log(len(b), "bytes of data read")
		s.m_readData += b
		while True:
			len: int = processReadData(s.m_readData);
			log(len,"bytes of" , len(s.m_readData), "processed")
		if(len > 0):
			s.m_readData = s.m_readData[:len]
		else:
			break;

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
