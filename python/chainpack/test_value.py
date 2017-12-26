#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

try:
	import better_exceptions
except:
	pass
from hypothesis import given
from hypothesis.strategies import *

from value import *

def test1():
	print("============= chainpack binary test ============")
	assert TypeInfo.Null_Array.value == 198

def test2():
	for t in range(TypeInfo.TERM, TypeInfo.TRUE+1):
		print(t, Blob(t), TypeInfo(t))

def test3():
	for t in range(TypeInfo.Null, TypeInfo.MetaIMap+1):
		print(t, Blob(t), TypeInfo(t))

def testNull():
	print("------------- NULL")

def testTinyUint():
	print("------------- tiny uint")
	for n in range(64):
		cp1 = RpcValue(n);
		out = Blob()
		len = out.write(cp1)
		if(n < 10):
			print(n, " ", cp1, " len: ", len, " dump: ", out)
		assert len == 1
		cp2 = out.read()
		assert cp1.type == cp2.type
		assert cp1.value == cp2.value

#"------------- uint"

def testIMap():
	print("------------- IMap")
	map = RpcValue(dict([
		(1, "foo "),
		(2, "bar"),
		(3, "baz")]), Type.IMap)
	cp1 = RpcValue(map)
	out = Blob()
	len = out.write(cp1)
	cp2 = out.read()
	print(cp1, cp2, " len: ", len, " dump: ", out)
	assert cp1, cp2

def testIMap2():
	cp1 = RpcValue(dict([
		(127, RpcValue([11,12,13])),
		(128, 2),
		(129, 3)]), Type.IMap)
	out = Blob()
	l: int = out.write(cp1)
	cp2: RpcValue = out.read()
	print(cp1," " ,cp2," len: " ,l ," dump: " ,out);
	assert cp1 == cp2
	assert cp1.type == cp2.type
	assert cp1.toIMap() == cp2.toIMap()

def testMeta():
	print("------------- Meta")
	cp1 = RpcValue([17, 18, 19])
	cp1.setMetaValue(Tag.MetaTypeNameSpaceId, RpcValue(1, Type.UInt))
	cp1.setMetaValue(Tag.MetaTypeId, RpcValue(2, Type.UInt))
	cp1.setMetaValue(Tag.USER, "foo")
	cp1.setMetaValue(Tag.USER+1, RpcValue([1,2,3]))
	out = Blob()
	len = out.write(cp1)
	orig_len = len(out)
	orig_out = out
	cp2 = out.read();
	consumed = orig_len - len(out)
	print(cp1, cp2, " len: ", len, " consumed: ", consumed , " dump: " , orig_out)
	assert len == consumed
	assert cp1.type() == cp2.type()
	assert cp1.metaData() == cp2.metaData()

def encode(x):
	return Blob(x)

def decode(blob):
	return blob.read()

json = recursive(none() | booleans() | floats() | integers() | text(),
lambda children: lists(children) | dictionaries(text(), children))

@given(json)
def test_decode_inverts_encode(s):
	s = RpcValue(s)
	assert decode(encode(s)) == s

@given(dictionaries(integers(1), json), json)
def test_decode_inverts_encode2(md, s):
	s = RpcValue(s)
	for k,v in md:
		if k in [Tag.MetaTypeId, Tag.MetaTypeNameSpaceId]:
			if (type(v) != int) or (v < 0):
				should_fail = True
		s.setMetaValue(k, v)
	try:
		assert decode(encode(s)) == s
	except ChainpackException as e:
		if not should_fail:
			raise



