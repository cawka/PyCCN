## -*- Mode: python; py-indent-offset: 4; indent-tabs-mode: nil; coding: utf-8; -*-
#
# Copyright (c) 2012-2013, Regents of the University of California
# BSD license, See the COPYING file for more information
# Written by: Derek Kulinski <takeda@takeda.tk>
#             Jeff Burke <jburke@ucla.edu>
#             Alexander Afanasyev <alexander.afanasyev@ucla.edu>
#

import _ndn
from Key import Key

from copy import copy
import time, struct, random

class Name (object):
    __slots__ = ['components', 'ccn_data']

    def __init__ (self, 
                  value = None):
        """
        Create Name object either from URI, another name, or list of name components
        """
        
        if not value:
            self.components = []

        # Copy Name from another Name object
        elif isinstance (value, Name):
            self.components = copy (value.components)

        # Name as string (URI)
        elif type (value) is str:
            self.components = _ndn.name_comps_from_ccn (_ndn.name_from_uri (value))

        # Name from list
        elif type (value) is list:
            self.components = copy (value)
        else:
            raise TypeError ("Only Name, string, or list can be supplied as an argument to Name constructor")

    @staticmethod
    def fromWire (wire):
        """
        Create Name object from wire representation
        """
        
        name = Name ()
        name.components = _ndn.name_comps_from_ccn_buffer (bytes (wire))
        return name

    def toWire (self):
        """
        Convert to wire representation
        """
        return _ndn.dump_charbuf (self.ccn_data)

    def toUri (self):
        """
        Convert to URI representation
        """
        return _ndn.name_to_uri (self.ccn_data)

    def __setattr__ (self, name, value):
        if name == "components":
            object.__setattr__ (self, 'ccn_data', None)
            object.__setattr__ (self, name, value)
        else:
            raise TypeError ("Only 'components' can be set explicitly updated")

    def __getattribute__(self, name):
        if name == "ccn_data":
            if not object.__getattribute__ (self, 'ccn_data'):
                object.__setattr__ (self, 'ccn_data', _ndn.name_comps_to_ccn (self.components))

        return object.__getattribute__ (self, name)

    def _append(self, component):
        components = copy (self.components)
        components.append (component)
        return Name (components)

    def append(self, value):
        components = copy(self.components)
        if isinstance (value, Name):
            components.extend (value.components)
        elif type (value) is list:
            components.extend (value)
        else:
            components.append (bytes (value))

        return Name (components)

    def appendKeyID(self, digest):
        if isinstance(digest, Key):
            digest = digest.publicKeyID

        component = b'\xc1.M.K\x00'
        component += digest

        return self._append(component)

    def appendVersion (self, version = None):
        if not version:
            inttime = int(time.time() * 4096 + 0.5)
            bintime = struct.pack("!Q", inttime)
            version = bintime.lstrip(b'\x00')
        component = b'\xfd' + version

        return self._append(component)

    def appendSegment(self, segment):
        return self._append(self.num2seg(segment))

    def appendNonce(self):
        val = random.getrandbits(64)
        component = b'\xc1.N\x00' + struct.pack("@Q", val)

        return self._append(component)

    def __repr__(self):
        return "ndn.Name('" + _ndn.name_to_uri (self.ccn_data) + "')"

    def __str__(self):
        return _ndn.name_to_uri (self.ccn_data)

    def __len__(self):
        return len (self.components)

    def __add__(self, other):
        return self.append (other)

    def __delattr__ (self, name, value):
        raise TypeError("can't modify immutable instance")

    def __getitem__(self, key):
        if type(key) is int:
            return self.components[key]
        elif type(key) is slice:
            return Name(self.components[key])
        else:
            raise ValueError("Unknown __getitem__ type: %s" % type(key))

    def __setitem__(self, key, value):
        self.components[key] = value

    def __delitem__(self, key):
        del self.components[key]

    def __len__(self):
        return len(self.components)

    def __lt__(self, other):
        return _ndn.compare_names (self.ccn_data, other.ccn_data) < 0

    def __gt__(self, other):
        return _ndn.compare_names (self.ccn_data, other.ccn_data) > 0

    def __eq__(self, other):
        return _ndn.compare_names (self.ccn_data, other.ccn_data) == 0

    def __le__(self, other):
        return _ndn.compare_names (self.ccn_data, other.ccn_data) <= 0

    def __ge__(self, other):
        return _ndn.compare_names (self.ccn_data, other.ccn_data) >= 0

    def __ne__(self, other):
        return _ndn.compare_names (self.ccn_data, other.ccn_data) != 0

    @staticmethod
    def num2seg (num):
        return b'\x00' + struct.pack('!Q', num).lstrip(b'\x00')

    @staticmethod
    def seg2num (segment):
        return long(struct.unpack("!Q", (8 - len(segment)) * "\x00" + segment)[0])

    def isPrefixOf (self, other):
        return self[:] == other[:len(self)]
