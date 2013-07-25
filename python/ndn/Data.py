## -*- Mode: python; py-indent-offset: 4; indent-tabs-mode: nil; coding: utf-8; -*-
#
# Copyright (c) 2011-2013, Regents of the University of California
# BSD license, See the COPYING file for more information
# Written by: Derek Kulinski <takeda@takeda.tk>
#             Jeff Burke <jburke@ucla.edu>
#

import _ndn

import utils
from utils import Const
from Name import Name
from SignedInfo import SignedInfo
from Signature import Signature

class Data (object):
    def __init__ (self, name = None, content = None, signed_info = None):
        if isinstance (name, Name):
            self.name = name
        else:
            self.name = Name (name)

        self.content = content
        self.signedInfo = signed_info or SignedInfo ()

        # generated
        self.signature = None

    # this is the finalization step
    # must pass a key here, there is no "default key" because
    # an NDN Face is not required to create the content object
    # thus there is no access to the ccn library keystore.
    #
    def sign(self, key):
        self.ccn_data = _ndn.encode_Data (self, 
                                                   self.name.ccn_data,
                                                   self.content, 
                                                   self.signedInfo.ccn_data, key)
        
    @staticmethod
    def fromWire (wire):
        return _ndn.Data_obj_from_ccn_buffer (wire)

    def toWire (self):
        """
        Convert Data packet to wire format

        Note that packet MUST be signed (or has been created from wire) before this call can succeed
        """
        return _ndn.dump_charbuf (self.ccn_data)

    def __setattr__(self, name, value):
        if name != "ccn_data":
            object.__setattr__ (self, 'ccn_data', None)

        if name == 'content':
            object.__setattr__(self, name, _ndn.content_to_bytes (value))
        else:
            object.__setattr__(self, name, value)

        object.__setattr__ (self, name, value)

    def __getattribute__(self, name):
        if name == "ccn_data":
            if not object.__getattribute__ (self, 'ccn_data'):
                object.__setattr__ (self, 'ccn_data', _ndn.Interest_obj_to_ccn (self))
        # elif name == "exclude":
        #     return Exclude.ConstExclude (object.__getattribute__ (self, name))

        return object.__getattribute__ (self, name)

    def __getattribute__(self, name):
        if name == "ccn_data":
            if not object.__getattribute__ (self, "ccn_data"):
                raise DataException ("Wire requested before Data packet is signed (use 'sign' call with appropriate key)")
        elif name == "name" or name == "signedInfo":
            return Const (object.__getattribute__ (self, name))

        return object.__getattribute__(self, name)

    def digest(self):
        return _ndn.digest_contentobject(self.ccn_data)

    def verify_content(self, handle):
        return _ndn.verify_content(handle.ccn_data, self.ccn_data)

    def verify_signature(self, key):
        return _ndn.verify_signature(self.ccn_data, key.ccn_data_public)

    def matchesInterest(self, interest):
        return _ndn.content_matches_interest(self.ccn_data, interest.ccn_data)
    
    # Where do we support versioning and segmentation?

    def __str__(self):
        ret = []
        ret.append("Name: %s" % self.name)
        ret.append("Content: %r" % self.content)
        ret.append("SignedInfo: %s" % self.signedInfo)
        ret.append("Signature: %s" % self.signature)
        return "\n".join(ret)

    def __repr__(self):
        args = []

        if self.name is not None:
            args += ["name=%r" % self.name]

        if self.content is not None:
            args += ["content=%r" % self.content]

        if self.signedInfo is not None:
            args += ["signed_info=%r" % self.signedInfo]

        if self.signature is not None:
            args += ["<signed>"]

        return "ndn.Data(%s)" % ", ".join(args)

class DataException (Exception):
    pass

