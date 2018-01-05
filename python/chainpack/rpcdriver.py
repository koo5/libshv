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
	PROTOCOL_VERSION = 1;
	m_messageReceivedCallback = None
	
	def sendMessage(msg: RpcValue):
		out = ChainPackProtocol()
		out.write(msg)
		log("send message: packed data: ",  (if packed_data.size() > 50: str(out[:50]) + "<... long data ...>") else out))
		enqueueDataToSend(out);


	def enqueueDataToSend(chunk_to_enqueue: Chunk):
		if(len(chunk_to_enqueue))
			m_chunkQueue.append(chunk_to_enqueue[:]));
		if(!isOpen()):
			logger.critical("write data error, socket is not open!")
			return
		flushNoBlock();
		writeQueue();


	def writeQueue(s):
		if(!len(s.m_chunkQueue)):
			return;
		log("writePendingData(), HI prio queue len: %s" % len(s.m_chunkQueue))
		#//static int hi_cnt = 0;
		chunk: Chunk = s.m_chunkQueue[0];

		if s.m_headChunkBytesWrittenSoFar == 0:
			protocol_version_data = ChainPackProtocol(RpcValue(PROTOCOL_VERSION, Type.UInt))
			packet_len_data = ChainPackProtocol(RpcValue(len(protocol_version_data) + len(chunk), Type.UInt))
			written_len = writeBytes(packet_len_data, len(packet_len_data));
			if(written_len < 0):
				raise Exception("Write socket error!");
			if written_len < len(packet_len_data):
				raise Exception("Design error! Chunk length shall be always written at once to the socket");
			
			l = writeBytes(protocol_version_data, len(protocol_version_data));
			if(l < 0):
				raise Exception("Write socket error!");
			if(l != 1)
				raise Exception("Design error! Protocol version shall be always written at once to the socket");

		l = writeBytes(chunk[s.m_headChunkBytesWrittenSoFar:])
		if(l < 0):
			raise Exception("Write socket error!");
		if(l == 0):
			raise Exception("Design error! At least 1 byte of data shall be always written to the socket");

		log("writeQueue - data len:", len(chunk),  "start index:", s.m_headChunkBytesWrittenSoFar, "bytes written:", l, "remaining:", (len(chunk) - s.m_headChunkBytesWrittenSoFar - l);
		s.m_headChunkBytesWrittenSoFar += l;
		if(s.m_headChunkBytesWrittenSoFar == len(chunk)):
			s.m_headChunkBytesWrittenSoFar = 0;
			s.m_chunkQueue.pop_front();


	def bytesRead(s, b: bytes):
		log(len(b), "bytes of data read")
		s.m_readData += b
		while True:
			l: int = processReadData(s.m_readData);
			log(l, "bytes of" , len(s.m_readData), "processed")
		if(l > 0):
			s.m_readData = s.m_readData[:l]
		else:
			break;


	def tryReadUIntData(s, input):
		try:
			return True, read_UIntData(input);
		except DeserializationException:
			return False, -1


	def processReadData(read_data: bytes) -> int:
		log("processReadData data len:", len(read_data))
		initial_len = len(read_data)
		input = ChainPackProtocol(read_data)
		ok, chunk_len = s.tryRead_UIntData(input);
		if not ok:
			return 0;
		ok, protocol_version:int = s.tryReadUIntData(input);
		if not ok:
			return 0;
		if protocol_version != PROTOCOL_VERSION:
			raise Exception("Unsupported protocol version");
		if(chunk_len > len(input)):
			return 0;
		msg: RpcValue = input.read()
		onMessageReceived(msg);
		return initial_len - len(input);


	def onMessageReceived(msg: RpcValue):
		log("\t emitting message received:" ,msg);
		if(s.m_messageReceivedCallback):
			s.m_messageReceivedCallback(msg);






#include "socketrpcdriver.h"
#include "../core/log.h"

#include <cassert>
#include <string.h>

#ifdef FREE_RTOS
#include "lwip/netdb.h"
#include "lwip/sockets.h"
#elif defined __unix
#include <unistd.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#endif

namespace cp = shv::core::chainpack;

namespace shv {
namespace core {
namespace chainpack {

SocketRpcDriver::SocketRpcDriver()
{
}

SocketRpcDriver::~SocketRpcDriver()
{
	closeConnection();
}

void SocketRpcDriver::closeConnection()
{
	if(isOpen())
		::close(m_socket);
	m_socket = -1;
}

bool SocketRpcDriver::isOpen()
{
	return m_socket >= 0;
}

size_t SocketRpcDriver::bytesToWrite()
{
	return m_bytesToWrite.length();
}

int64_t SocketRpcDriver::writeBytes(const char *bytes, size_t length)
{
	if(!isOpen()) {
		shvInfo() << "Write to closed socket";
		return 0;
	}
	flushNoBlock();
	size_t bytes_to_write_len = (m_bytesToWrite.size() + length > m_maxBytesToWriteLength)? m_maxBytesToWriteLength - m_bytesToWrite.size(): length;
	if(bytes_to_write_len > 0)
		m_bytesToWrite += std::string(bytes, bytes_to_write_len);
	flushNoBlock();
	return bytes_to_write_len;
}

bool SocketRpcDriver::flushNoBlock()
{
	if(m_bytesToWrite.empty()) {
		shvDebug() << "write buffer is empty";
		return false;
	}
	shvDebug() << "Flushing write buffer, buffer len:" << m_bytesToWrite.size() << "...";
	int64_t n = ::write(m_socket, m_bytesToWrite.data(), m_bytesToWrite.length());
	shvDebug() << "\t" << n << "bytes written";
	if(n > 0)
		m_bytesToWrite = m_bytesToWrite.substr(n);
	return (n > 0);
}

bool SocketRpcDriver::connectToHost(const std::string &host, int port)
{
	closeConnection();
	m_socket = socket(AF_INET, SOCK_STREAM, 0);
	if (m_socket < 0) {
		 shvError() << "ERROR opening socket";
		 return false;
	}
	{
		struct sockaddr_in serv_addr;
		struct hostent *server;
		server = gethostbyname(host.c_str());

		if (server == NULL) {
			shvError() << "ERROR, no such host" << host;
			return false;
		}

		bzero((char *) &serv_addr, sizeof(serv_addr));
		serv_addr.sin_family = AF_INET;
		bcopy((char *)server->h_addr, (char *)&serv_addr.sin_addr.s_addr, server->h_length);
		serv_addr.sin_port = htons(port);

		/* Now connect to the server */
		shvInfo().nospace() << "connecting to " << host << ":" << port;
		if (::connect(m_socket, (struct sockaddr*)&serv_addr, sizeof(serv_addr)) < 0) {
			shvError() << "ERROR, connecting host" << host;
			return false;
		}
	}


	{
		//set_socket_nonblock
		int flags;
		flags = fcntl(m_socket,F_GETFL,0);
		assert(flags != -1);
		fcntl(m_socket, F_SETFL, flags | O_NONBLOCK);
	}

	shvInfo() << "... connected";

	return true;
}

void SocketRpcDriver::exec()
{
	//int pfd[2];
	//if (pipe(pfd) == -1)
	//		 return;
	fd_set read_flags,write_flags; // the flag sets to be used
	struct timeval waitd;

	static constexpr size_t BUFF_LEN = 255;
	char in[BUFF_LEN];
	char out[BUFF_LEN];
	memset(&in, 0, BUFF_LEN);
	memset(&out, 0, BUFF_LEN);

	while(1) {
		waitd.tv_sec = 5;
		waitd.tv_usec = 0;

		FD_ZERO(&read_flags);
		FD_ZERO(&write_flags);
		FD_SET(m_socket, &read_flags);
		if(!m_bytesToWrite.empty())
			FD_SET(m_socket, &write_flags);
		//FD_SET(STDIN_FILENO, &read_flags);
		//FD_SET(STDIN_FILENO, &write_flags);

		//ESP_LOGI(__FILE__, "select ...");
		int sel = select(FD_SETSIZE, &read_flags, &write_flags, (fd_set*)0, &waitd);

		//ESP_LOGI(__FILE__, "select returned, number of active file descriptors: %d", sel);
		//if an error with select
		if(sel < 0) {
			shvError() << "select failed errno:" << errno;
			return;
		}
		if(sel == 0) {
			shvInfo() << "\t timeout";
			idleTaskOnSelectTimeout();
			continue;
		}

		//socket ready for reading
		if(FD_ISSET(m_socket, &read_flags)) {
			shvInfo() << "\t read fd is set";
			//clear set
			FD_CLR(m_socket, &read_flags);

			memset(&in, 0, BUFF_LEN);

			auto n = read(m_socket, in, BUFF_LEN);
			shvInfo() << "\t " << n << "bytes read";
			if(n <= 0) {
				shvError() << "Closing socket";
				closeConnection();
				return;
			}
			bytesRead(std::string(in, n));

		}

		//socket ready for writing
		if(FD_ISSET(m_socket, &write_flags)) {
			shvInfo() << "\t write fd is set";
			FD_CLR(m_socket, &write_flags);
			enqueueDataToSend(Chunk());
		}
	}
}

void SocketRpcDriver::sendResponse(int request_id, const cp::RpcValue &result)
{
	cp::RpcResponse resp;
	resp.setId(request_id);
	resp.setResult(result);
	shvInfo() << "sending response:" << resp.toStdString();
	sendMessage(resp.value());
}

void SocketRpcDriver::sendNotify(std::string &&method, const cp::RpcValue &result)
{
	shvInfo() << "sending notify:" << method;
	cp::RpcNotify ntf;
	ntf.setMethod(std::move(method));
	ntf.setParams(result);
	sendMessage(ntf.value());
}
