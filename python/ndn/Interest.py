## -*- Mode: python; py-indent-offset: 4; indent-tabs-mode: nil; coding: utf-8; -*-
#
# Copyright (c) 2011, Regents of the University of California
# BSD license, See the COPYING file for more information
# Written by: Derek Kulinski <takeda@takeda.tk>
#             Jeff Burke <jburke@ucla.edu>
#             Alexander Afanasyev <alexander.afanasyev@ucla.edu>
#

import _pyndn

import utils
from utils import Const
from Name import Name

class Interest(object):
    def __init__ (self, name = None, minSuffixComponents = None,
                  maxSuffixComponents = None, publisherPublicKeyDigest = None,
                  exclude = None, childSelector = None, answerOriginKind = None,
                  scope = None, interestLifetime = None, nonce = None):
        
        if isinstance (name, Name):
            self.name = name  # Start from None to use for templates?
        else:
            self.name = Name (name)
        
        self.minSuffixComponents = minSuffixComponents  # default 0
        self.maxSuffixComponents = maxSuffixComponents  # default infinity
        self.publisherPublicKeyDigest = publisherPublicKeyDigest  # SHA256 hash
        self.exclude = exclude
        self.childSelector = childSelector
        self.answerOriginKind = answerOriginKind
        self.scope = scope
        self.interestLifetime = interestLifetime
        self.nonce = nonce

    # @staticmethod
    # def fromWire (wire):
    #     interest = Interest ()
    #     interest.components = _pyndn.Interest_obj_from_buffer (wire))
    #     return interest

    def toWire (self):
        return _pyndn.dump_charbuf (self.ndn_data)

    def __setattr__(self, name, value):
        if name != "ndn_data":
            object.__setattr__ (self, 'ndn_data', None)

        object.__setattr__ (self, name, value)

    def __getattribute__(self, name):
        if name == "ndn_data":
            if not object.__getattribute__ (self, 'ndn_data'):
                object.__setattr__ (self, 'ndn_data', _pyndn.Interest_obj_to_ndn (self))
        elif name == "name":
            return Const (object.__getattribute__ (self, name))
        # elif name == "exclude":
        #     return Exclude.ConstExclude (object.__getattribute__ (self, name))

        return object.__getattribute__ (self, name)

    def __str__(self):
        res = []
        res.append("name: %s" % self.name)
        res.append("minSuffixComponents: %s" % self.minSuffixComponents)
        res.append("maxSuffixComponents: %s" % self.maxSuffixComponents)
        res.append("publisherPublicKeyDigest: %r" % self.publisherPublicKeyDigest)
        res.append("exclude:\n%s" % self.exclude)
        res.append("childSelector: %s" % self.childSelector)
        res.append("answerOriginKind: %s" % self.answerOriginKind)
        res.append("scope: %s" % self.scope)
        res.append("interestLifetime: %s" % self.interestLifetime)
        res.append("nonce: %r" % self.nonce)
        return "\n".join(res)

    def __repr__(self):
        args = []

        if self.name is not None:
            args += ["name=%r" % str(self.name)]
        if self.minSuffixComponents is not None:
            args += ["minSuffixComponents=%r" % self.minSuffixComponents]
        if self.maxSuffixComponents is not None:
            args += ["maxSuffixComponents=%r" % self.maxSuffixComponents]
        if self.publisherPublicKeyDigest is not None:
            args += ["publisherPublicKeyDigest=%r" % self.publisherPublicKeyDigest]
        if self.exclude is not None:
            args += ["exclude=%r" % self.exclude]
        if self.childSelector is not None:
            args += ["childSelector=%r" % self.childSelector]
        if self.answerOriginKind is not None:
            args += ["answerOriginKind=%r" % self.answerOriginKind]
        if self.scope is not None:
            args += ["scope=%r" % self.scope]
        if self.interestLifetime is not None:
            args += ["interestLifetime=%r" % self.interestLifetime]
        if self.nonce is not None:
            args += ["nonce=%r" % self.nonce]

        return "ndn.Interest(%s)" % ", ".join(args)

    def get_aok_value(self):
        global AOK_DEFAULT

        return AOK_DEFAULT if not self.answerOriginKind else self.answerOriginKind

    def matches_name(self, name):
        i_name = self.name.components
        o_name = name.components

        # requested name is longer than ours
        if len(i_name) > len(o_name):
            return False

        # at least one of given components don't match
        if not all(i == j for i, j in zip(i_name, o_name)):
            return False

        return True

class AOKType(utils.Flag):
    _prefix = "ndn"

AOK_NONE = AOKType.new_flag('AOK_NONE', 0x0)
AOK_CS = AOKType.new_flag('AOK_CS', 0x1)  # Answer from content store
AOK_NEW = AOKType.new_flag('AOK_NEW', 0x2)  # OK to produce new content
AOK_STALE = AOKType.new_flag('AOK_STALE', 0x4)  # OK to answer with stale data
AOK_EXPIRE = AOKType.new_flag('AOK_EXPIRE', 0x10) # Mark as stale (requires scope 0)

AOK_DEFAULT = AOK_CS | AOK_NEW

CHILD_SELECTOR_LEFT = 0
CHILD_SELECTOR_RIGHT = 1

#
#    //  IMPORTANT:  Exclusion component list must be sorted following "Canonical NDNx ordering"
#    //              http://www.ndnx.org/releases/latest/doc/technical/CanonicalOrder.html
#    //              in which shortest components go first.
#

# # Bloom filters will be deprecated, so we do not support them.
# class ExclusionFilter(object):
#     def __init__(self):
#         self.components = []

#         # py-ndn
#         self.ndn_data_dirty = False
#         self.ndn_data = None  # backing charbuf

#     def reset(self):
#         self.components = []

#     def add_names(self, names):
#         self.ndn_data_dirty = True
#         self.components.extend(sorted(names))

#     def add_name(self, name):
#         if not type(name) is Name.Name:
#             raise TypeError("Name type required")

#         self.ndn_data_dirty = True
#         self.components.append(name)

#     def add_any(self):
#         self.components.append(Name.Name(name_type = Name.NAME_ANY))

#     def __setattr__(self, name, value):
#         if name != "ndn_data_dirty":
#             self.ndn_data_dirty = True
#         object.__setattr__(self, name, value)

#     def __getattribute__(self, name):
#         if name == "ndn_data":
#             if object.__getattribute__(self, 'ndn_data_dirty'):
#                 self.ndn_data = _pyndn.ExclusionFilter_names_to_ndn(
#                     self.components)
#                 self.ndn_data_dirty = False
#         return object.__getattribute__(self, name)

#     def __str__(self):
#         comps = []
#         for n in self.components:
#             comps.append(str(n))
#         return str(comps)
