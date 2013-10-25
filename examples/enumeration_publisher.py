#! /usr/bin/env python

#
# Copyright (c) 2011, Regents of the University of California
# BSD license, See the COPYING file for more information
# Written by: Derek Kulinski <takeda@takeda.tk>
#

import sys
import ndn
from ndn.impl.enumeration import ndnb_enumerate
from ndn.impl.segmenting import segmenter, Wrapper

def generate_names():
	names = ["/Hello", "/World", "/This", "/is", "/an", "/enumeration", "/example"]
	return map(lambda x: ndn.Name(x), names)

def main(args):
	if len(sys.argv) != 2:
		usage()

	name = ndn.Name(sys.argv[1])
	data = ndnb_enumerate(generate_names())

	key = ndn.Face.getDefaultKey()
	name = name.append('\xc1.E.be').appendKeyID(key).appendVersion()

	wrapper = Wrapper(name, key)
	sgmtr = segmenter(data, wrapper)

	handle = ndn.Face()
	for seg in sgmtr:
		handle.put(seg)

	return 0

def usage():
	print("Usage: %s <uri>" % sys.argv[0])
	sys.exit(1)

if __name__ == '__main__':
	sys.exit(main(sys.argv))
