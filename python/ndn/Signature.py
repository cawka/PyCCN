## -*- Mode: python; py-indent-offset: 4; indent-tabs-mode: nil; coding: utf-8; -*-
#
# Copyright (c) 2011-2013, Regents of the University of California
# BSD license, See the COPYING file for more information
# Written by: Derek Kulinski <takeda@takeda.tk>
#             Jeff Burke <jburke@ucla.edu>
#             Alexander Afanasyev <alexander.afanasyev@ucla.edu>
#

import _ndn

class Signature(object):
    def __init__(self):
        self.witness = None
        self.signatureBits = None

    def __setattr__(self, name, value):
        if name != "ccn_data":
            object.__setattr__ (self, 'ccn_data', None)

        object.__setattr__ (self, name, value)

    def __getattribute__(self, name):
        if name == "ccn_data":
            if not object.__getattribute__ (self, 'ccn_data'):
                self.ccn_data = _ndn.Signature_obj_to_ccn(self)

        return object.__getattribute__ (self, name)

    def __str__(self):
        res = []
        res.append("witness = %s" % self.witness)
        res.append("signatureBits = %r" % self.signatureBits)
        return "\n".join(res)
