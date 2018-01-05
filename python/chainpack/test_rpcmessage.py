#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
try:
	import better_exceptions
except:
	pass
from rpcmessage import *

def testRpcRequest():
		print("============= chainpack rpcmessage test ============\n")
		print("------------- RpcRequest")
		rq = RpcRequest()
		rq.setId(123)
		rq.setMethod("foo")
		rq.setParams({"a": 45,
		            "b": "bar",
					"c": RpcValue([1,2,3])})
		rq.setMetaValue(RpcMessage.Tag.DeviceId, "aus/mel/pres/A");

		cp1 = rq.value
		out = ChainPackProtocol()
		len = rq.write(out);
		RpcValue: cp2 = out.read()
		print (cp1, " " ,cp2," len: " << len << " dump: " ,out);
		assert cp1.type == cp2.type
		RpcRequest: rq2(cp2);
		assert rq2.isRequest()
		assert rq2.id == rq.id
		assert rq2.method == rq.method
		assert rq2.params == rq.params

def testRpcResponse():
		print("------------- RpcResponse")
		RpcResponse: rs;
		rs.setId(123).setResult(42);
		out = ChainPackProtocol()
		RpcValue: cp1 = rs.value()
		int: len = out.write(rs)
		RpcValue: cp2 = out.read()
		print(cp1 + " " + cp2 +" len: " + len + " dump: " + str(out));
		assert cp1.type() == cp2.type()
		RpcResponse: rs2 = RpcResponse(cp2);
		assert rs2.isResponse()
		assert rs2.id() == rs.id()
		assert rs2.result() == rs.result()


def testRpcResponse2():
	rs = RpcResponse()
	rs.setId(123)
	rs.setError(RpcResponse.Error.createError(RpcResponse.Error.InvalidParams, "Paramter length should be greater than zero!"))
	out = ChainPackProtocol()
	cp1: RpcValue = rs.value();
	l: int = rs.write(out);
	cp2: Value = out.read()
	print(cp1, " ", cp2, " len: ", l, " dump: ", out);
	assert(cp1.type() == cp2.type());
	rs2 = RpcResponse(cp2);
	assert(rs2.isResponse());
	assert rs2.id() == rs.id()
	assert rs2.error() == rs.error()

def testRpcNotify():
	print("------------- RpcNotify")
	rq = RpcRequest()
	rq.setMethod("foo").setParams({
						   "a": 45,
						   "b": "bar",
						   "c": RpcValue([1,2,3])});
	out = ChainPackProtocol()
	cp1: Value = rq.value();
	l: int = out.write(rq);
	cp2: Value = out.read()
	print(cp1," " ,cp2," len: " ,l ," dump: " ,out);
	assert(cp1.type() == cp2.type());
	rq2 = RpcRequest(cp2);
	assert(rq2.isNotify());
	assert rq2.method() == rq.method()
	assert rq2.params() == rq.params()
