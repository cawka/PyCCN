## -*- Mode: python; py-indent-offset: 4; indent-tabs-mode: nil; coding: utf-8; -*-
#
# Copyright (c) 2011, Regents of the University of California
# BSD license, See the COPYING file for more information
# Written by: Derek Kulinski <takeda@takeda.tk>
#             Jeff Burke <jburke@ucla.edu>
#

__all__ = ['Face', 'Name', 'Interest', 'Data', 'Key']

VERSION = 0.4

try:
    from Face import Face
    from Name import Name
    from Interest import Interest
    from Data import Data
    from Key import Key

    from EventLoop import EventLoop
    from KeyLocator import KeyLocator
    from SignedInfo import SignedInfo, CONTENT_DATA, CONTENT_ENCR, CONTENT_GONE, CONTENT_KEY, CONTENT_LINK, CONTENT_NACK
    from Signature import Signature
    
    from ndn import NameCrypto
    from ndn.LocalPrefixDiscovery import LocalPrefixDiscovery

except ImportError:
    import sys as _sys
    del _sys.modules [__name__]
    del _sys
    raise

def name_compatibility ():
    global _name_immutable

    _name_immutable = 1
