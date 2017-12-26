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
	m_messageReceivedCallback = None
	
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

	def tryReadUIntData(s, in):
		try:
			return True, read_UIntData(in);
		except DeserializationException:
			return False, -1

	def processReadData(read_data: bytes) -> int:
		log("data len:", len(read_data))
		initial_len = len(read_data)
		in = Blob(read_data)
		ok, chunk_len = s.tryRead_UIntData(in);
		if not ok:
			return 0;
		ok, protocol_version:int = s.tryReadUIntData(in);
		if not ok:
			return 0;
		if protocol_version != PROTOCOL_VERSION:
			raise Exception("Unsupported protocol version");
		if(chunk_len > len(in)):
			return 0;
		msg: RpcValue = in.read()
		onMessageReceived(msg);
		return initial_len - len(in);

	def onMessageReceived(msg: RpcValue):
		log("\t emitting message received:" ,msg);
		if(s.m_messageReceivedCallback):
			s.m_messageReceivedCallback(msg);
