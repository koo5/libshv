#!/usr/bin/python3.6
# -*- coding: utf-8 -*-

HOST, PORT = "127.0.0.1", 6016

import sys
import socket
from threading import Thread
from queue import Queue, Empty
import socketserver


import logging
logger=logging.getLogger()

from utils import _print

def log(*vargs):
	logger.debug(_print(*vargs))

def info(*vargs):
	logger.info(_print(*vargs))


class MyTCPHandler(socketserver.BaseRequestHandler):
	def handle(self):
		print("handle")
		try:
			data = bytes()
			while True:
				inc = self.request.recv(240000)
				if len(inc) == 0:
					continue
				data += inc
				data_str = str(data, 'utf-8')
				if '\n' in data_str:
					print("{} wrote:".format(self.client_address[0]))
					print(data_str);
					sys.stdout.flush();
					self.request.sendall(data.upper())
					command_queue.put(data_str)
					send_thread_message()
					print("bye")
					return
		except Exception as e:
			print(str(e))
			return
		print("ThreadedTCPRequestHandler shutting down...")


server = socketserver.TCPServer((HOST, PORT), MyTCPHandler)
server.serve_forever()
