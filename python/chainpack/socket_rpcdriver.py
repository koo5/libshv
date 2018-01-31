#!/usr/bin/python3.6
# -*- coding: utf-8 -*-

import sys
import socket
from threading import Thread
from queue import Queue, Empty
import socketserver
import logging


logger=logging.getLogger()
from utils import print_to_string
def log(*vargs):
	logger.debug(print_to_string(*vargs))
def info(*vargs):
	logger.info(print_to_string(*vargs))



class SocketRpcDriver(RpcDriver):
	def bytesToWrite(s):
		return m_bytesToWrite.length();

	def writeBytes(s, b):
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

