#!/usr/bin/python3.6
# -*- coding: utf-8 -*-


HOST, PORT = "127.0.0.1", 6016


import sys
import socket
from threading import Thread
from queue import Queue, Empty
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



class MyTCPHandler(RpcDriver, socketserver.BaseRequestHandler):
	def handle(s):
		while True:
			s.bytesRead(s.request.recv(240000))

	def writeBytes(s, b):
		s.request.sendall(b)

	def onMessageReceived(msg: RpcValue):
		p = msg.toPython()
		s.sendResponse(p["id"], msg)



server = socketserver.TCPServer((HOST, PORT), MyTCPHandler)
server.serve_forever()
