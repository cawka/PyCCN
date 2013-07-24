## -*- Mode: python; py-indent-offset: 4; indent-tabs-mode: nil; coding: utf-8; -*-
#
# Copyright (c) 2011-2013, Regents of the University of California
# BSD license, See the COPYING file for more information
# Written by: Derek Kulinski <takeda@takeda.tk>
#             Jeff Burke <jburke@ucla.edu>
#             Alexander Afanasyev <alexander.afanasyev@ucla.edu>
#

import _ndn
import utils

class ContentType(utils.Enum):
    _prefix = "ndn"

CONTENT_DATA = ContentType.new_flag('CONTENT_DATA', 0x0C04C0)
CONTENT_ENCR = ContentType.new_flag('CONTENT_ENCR', 0x10D091)
CONTENT_GONE = ContentType.new_flag('CONTENT_GONE', 0x18E344)
CONTENT_KEY  = ContentType.new_flag('CONTENT_KEY',  0x28463F)
CONTENT_LINK = ContentType.new_flag('CONTENT_LINK', 0x2C834A)
CONTENT_NACK = ContentType.new_flag('CONTENT_NACK', 0x34008A)

class SignedInfo (object):
    def __init__(self, key_digest = None, key_locator = None, type = CONTENT_DATA,
                 freshness = None, final_block = None, py_timestamp = None,
                 timestamp = None):

        self.publisherPublicKeyDigest = key_digest

        if py_timestamp is not None:
            if timestamp:
                raise ValueError("You can define only timestamp or py_timestamp")
            self.timeStamp = utils.py2ccn_time (py_timestamp)
        else:
            self.timeStamp = timestamp

        self.type = type
        self.freshnessSeconds = freshness
        self.finalBlockID = final_block
        self.keyLocator = key_locator

    def __setattr__(self, name, value):
        if name != "ccn_data":
            object.__setattr__ (self, 'ccn_data', None)

        object.__setattr__ (self, name, value)

    def __getattribute__(self, name):
        if name == "ccn_data":
            if not object.__getattribute__ (self, 'ccn_data'):
                key_locator = self.keyLocator.ccn_data if self.keyLocator else None
                self.ccn_data = _ndn.SignedInfo_to_ccn (self.publisherPublicKeyDigest, self.type, self.timeStamp,
                                                        self.freshnessSeconds or (-1), self.finalBlockID, key_locator)
        elif name == "py_timestamp":
            ts = self.timeStamp
            if ts is None:
                return None
            return utils.ccn2py_time (ts)
        
        return object.__getattribute__ (self, name)

    def __repr__(self):
        args = []

        if self.publisherPublicKeyDigest is not None:
            args += ["key_digest=%r" % self.publisherPublicKeyDigest]
        if self.keyLocator is not None:
            args += ["key_locator=%r" % self.keyLocator]
        if self.type is not None:
            args += ["type=%r" % self.type]
        if self.freshnessSeconds is not None:
            args += ["freshness=%r" % self.freshnessSeconds]
        if self.finalBlockID is not None:
            args += ["final_block=%r" % self.finalBlockID]
        if self.timeStamp is not None:
            args += ["py_timestamp=%r" % self.py_timestamp]

        return "ndn.SignedInfo(%s)" % ", ".join(args)
