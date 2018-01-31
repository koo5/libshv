#!/usr/bin/python3.6
# -*- coding: utf-8 -*-


import socketserver
import logging
from rpcdriver import RpcDriver
from value import RpcValue


logger=logging.getLogger()
from utils import print_to_string
def log(*vargs):
	logger.debug(print_to_string(*vargs))
def info(*vargs):
	logger.info(print_to_string(*vargs))



class MyTCPHandler(socketserver.BaseRequestHandler):

	def handle(s):
		driver = RpcDriver()
		driver.writeBytes = s.writeBytes
		driver.onMessageReceived = s.onMessageReceived
		while True:
			driver.bytesRead(s.request.recv(240000))

	def writeBytes(s, b):
		s.request.sendall(b)

	def onMessageReceived(msg: RpcValue):
		p = msg.toPython()
		s.sendResponse(p["id"], msg)


def serve(host = "127.0.0.1", port=6016):
	server = socketserver.TCPServer((host, port), MyTCPHandler)
	print("serving on port ", server.socket.getsockname()[1])
	server.serve_forever()


if __name__ == "__main__":
	serve()

