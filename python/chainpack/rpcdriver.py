#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from value import *
import logging


logger=logging.getLogger()
logger.setLevel(logging.DEBUG)
from utils import print_to_string
def log(*vargs):
	logger.debug(print_to_string(*vargs))
def info(*vargs):
	logger.info(print_to_string(*vargs))


defaultRpcTimeout = 5000;

class RpcDriver():
	PROTOCOL_VERSION = 1;

	def __init__(s):
		s.m_readData = bytearray()

	def sendMessage(s, msg: RpcValue):
		chunk = ChainPackProtocol(msg)
		log("send message: packed data: ",  chunk[:50] + "<... long data ...>" if packed_data.size() > 50 else chunk)
		protocol_version_data = ChainPackProtocol(RpcValue(PROTOCOL_VERSION, Type.UInt))
		packet_len_data = ChainPackProtocol(out.write(RpcValue(len(protocol_version_data) + len(chunk), Type.UInt)))
		s.writeBytes(packet_len_data)
		s.writeBytes(protocol_version_data)
		s.writeBytes(chunk)

	def bytesRead(s, b: bytes):
		log(len(b), "bytes of data read")
		s.m_readData += b
		while True:
			l: int = s.processReadData(s.m_readData);
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

	def processReadData(s, read_data: bytes) -> int:
		log("processReadData data len:", len(read_data))
		initial_len = len(read_data)
		input = ChainPackProtocol(read_data)
		ok, chunk_len = s.tryRead_UIntData(input);
		if not ok:
			return 0;
		ok, protocol_version = s.tryReadUIntData(input);
		if not ok:
			return 0;
		if protocol_version != PROTOCOL_VERSION:
			raise Exception("Unsupported protocol version");
		if(chunk_len > len(input)):
			return 0;
		msg: RpcValue = input.read()
		s.onMessageReceived(msg);
		return initial_len - len(input);

	def sendResponse(s, request_id: int, result: RpcValue):
		resp = RpcResponse()
		resp.setId(request_id);
		resp.setResult(result);
		info("sending response:", resp)
		s.sendMessage(resp._value);

	def sendNotify(s, method: str, result: RpcValue):
		info("sending notify:%s", method)
		ntf = RpcNotify()
		ntf.setMethod(method);
		ntf.setParams(result);
		s.sendMessage(ntf._value);


	"""
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
			written_len = s.writeBytes(packet_len_data, len(packet_len_data));
			if(written_len < 0):
				raise Exception("Write socket error!");
			if written_len < len(packet_len_data):
				raise Exception("Design error! Chunk length shall be always written at once to the socket");
			
			l = s.writeBytes(protocol_version_data, len(protocol_version_data));
			if(l < 0):
				raise Exception("Write socket error!");
			if(l != 1)
				raise Exception("Design error! Protocol version shall be always written at once to the socket");

		l = s.writeBytes(chunk[s.m_headChunkBytesWrittenSoFar:])
		if(l < 0):
			raise Exception("Write socket error!");
		if(l == 0):
			raise Exception("Design error! At least 1 byte of data shall be always written to the socket");

		log("writeQueue - data len:", len(chunk),  "start index:", s.m_headChunkBytesWrittenSoFar, "bytes written:", l, "remaining:", (len(chunk) - s.m_headChunkBytesWrittenSoFar - l);
		s.m_headChunkBytesWrittenSoFar += l;
		if(s.m_headChunkBytesWrittenSoFar == len(chunk)):
			s.m_headChunkBytesWrittenSoFar = 0;
			s.m_chunkQueue.pop_front();
	"""
