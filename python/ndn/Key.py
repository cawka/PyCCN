## -*- Mode: python; py-indent-offset: 4; indent-tabs-mode: nil; coding: utf-8; -*-
#
# Copyright (c) 2011, Regents of the University of California
# BSD license, See the COPYING file for more information
# Written by: Derek Kulinski <takeda@takeda.tk>
#             Jeff Burke <jburke@ucla.edu>
#

import _ndn

class Key (object):
    def __init__ (self):
        self.type = None
        self.publicKeyID = None # SHA256 hash
        # ndn
        self.ccn_data_dirty = False
        self.ccn_data_public = None  # backing pkey
        self.ccn_data_private = None # backing pkey

    @staticmethod
    def createFromDER (private = None, public = None):
        key = Key ()
        key.fromDER (private, public)
        return key

    @staticmethod
    def createFromPEM (filename = None, private = None, public = None, password = None):
        key = Key ()
        key.fromPEM (filename, private, public, password)
        return key

    @staticmethod
    def getDefault ():
        return _ndn.get_default_key()

    def generateRSA(self, numbits):
        _ndn.generate_RSA_key(self, numbits)

    def privateToDER(self):
        if not self.ccn_data_private:
            raise _ndn.CCNKeyError("Key is not private")
        return _ndn.DER_write_key(self.ccn_data_private)

    def publicToDER(self):
        return _ndn.DER_write_key(self.ccn_data_public)

    def privateToPEM(self, filename = None, password = None):
        if not self.ccn_data_private:
            raise _ndn.CCNKeyError("Key is not private")

        if filename:
            f = open(filename, 'w')
            _ndn.PEM_write_key(self.ccn_data_private, file=f, password = password)
            f.close()
        else:
            return _ndn.PEM_write_key(self.ccn_data_private, password = password)

    def publicToPEM(self, filename = None):
        if filename:
            f = open(filename, 'w')
            _ndn.PEM_write_key(self.ccn_data_public, file=f)
            f.close()
        else:
            return _ndn.PEM_write_key(self.ccn_data_public)

    def fromDER(self, private = None, public = None):
        if private:
            (self.ccn_data_private, self.ccn_data_public, self.publicKeyID) = \
                _ndn.DER_read_key(private=private)
            return
        if public:
            (self.ccn_data_private, self.ccn_data_public, self.publicKeyID) = \
                _ndn.DER_read_key(public=public)
            return

    def fromPEM(self, filename = None, private = None, public = None, password = None):
        if filename:
            f = open(filename, 'r')
            (self.ccn_data_private, self.ccn_data_public, self.publicKeyID) = \
                _ndn.PEM_read_key(file=f, password = password)
            f.close()
        elif private:
            (self.ccn_data_private, self.ccn_data_public, self.publicKeyID) = \
                _ndn.PEM_read_key(private=private, password = password)
        elif public:
            (self.ccn_data_private, self.ccn_data_public, self.publicKeyID) = \
                _ndn.PEM_read_key(public=public)

    def __repr__ (self):
        return "ndn.Key(%s...)" % self.publicKeyID.encode('hex_codec')[0:10]
# plus library helper functions to generate and serialize keys?

