## -*- Mode: python; py-indent-offset: 4; indent-tabs-mode: nil; coding: utf-8; -*-
#
# Copyright (c) 2011, Regents of the University of California
# BSD license, See the COPYING file for more information
# Written by: Derek Kulinski <takeda@takeda.tk>
#             Jeff Burke <jburke@ucla.edu>
#             Alexander Afanasyev <alexander.afanasyev@ucla.edu>
#

# Upcall Result
RESULT_ERR               = -1 # upcall detected an error
RESULT_OK                =  0 # normal upcall return
RESULT_REEXPRESS         =  1 # reexpress the same interest again
RESULT_INTEREST_CONSUMED =  2 # upcall claims to consume interest
RESULT_VERIFY            =  3 # force an unverified result to be verified
RESULT_FETCHKEY          =  4 # request fetching of an unfetched key

# Upcall kind
UPCALL_FINAL              = 0 # handler is about to be deregistered
UPCALL_INTEREST           = 1 # incoming interest
UPCALL_CONSUMED_INTEREST  = 2 # incoming interest, someone has answered
UPCALL_CONTENT            = 3 # incoming verified content
UPCALL_INTEREST_TIMED_OUT = 4 # interest timed out
UPCALL_CONTENT_UNVERIFIED = 5 # content that has not been verified
UPCALL_CONTENT_BAD        = 6 # verification failed
UPCALL_CONTENT_KEYMISSING = 7 # key has not been fetched
UPCALL_CONTENT_RAW        = 8 # verification has not been attempted

# Fronts ccn_closure.

class Closure(object):
    def __init__(self):
        #I don't think storing CCN's closure is needed
        #and it creates a reference loop, as of now both
        #of those variables are never set -- Derek
        #
        # Use instance variables to return data to callback
        self.ccn_data = None  # this holds the ccn_closure
        self.ccn_data_dirty = False
        pass

    #If you're getting strange errors in upcall()
    #check your code whether you're returning a value
    def upcall(self, kind, upcallInfo):
        global RESULT_OK

        print('upcall', self, kind, upcallInfo)
        return RESULT_OK

class UpcallInfo(object):
    def __init__(self):
        self.ccn = None  # CCN object (not used)
        self.Interest = None  # Interest object
        self.matchedComps = None  # int
        self.Data = None  # Content object

    def __str__(self):
        ret = "ccn = %s" % self.ccn
        ret += "\nInterest = %s" % self.Interest
        ret += "\nmatchedComps = %s" % self.matchedComps
        ret += "\nData: %s" % str(self.Data)
        return ret

class TrivialExpressClosure (Closure):
    """
    Trivial closure that will notify about Data packet or Timeout via two separate callbacks

    If interest needs to be retransmitted, a separate expressInterest call must be issued
    (no reliance on return value)
    """
    __slots__ = ["onData", "onTimeout"]

    def __init__ (self, onData, onTimeout):
        super (TrivialExpressClosure, self).__init__ ()

        self.onData = onData
        self.onTimeout = onTimeout

    def upcall(self, kind, upcallInfo):
        if (kind == UPCALL_CONTENT or
            kind == UPCALL_CONTENT_UNVERIFIED or
            kind == UPCALL_CONTENT_UNVERIFIED or
            kind == UPCALL_CONTENT_KEYMISSING or
            kind == UPCALL_CONTENT_RAW):
            self.onData (upcallInfo.Interest, upcallInfo.Data)
        elif (kind == UPCALL_INTEREST_TIMED_OUT):
            if self.onTimeout:
                self.onTimeout (upcallInfo.Interest)

        # Always return RESULT_OK
        return RESULT_OK

class VersionResolverClosure (Closure):
    """
    Need to be debugged
    """

    __slots__ = ["face", "onData", "onTimeout", "foundVersion"]

    def __init__ (self, face, onData, onTimeout):
        super (VersionResolverClosure, self).__init__ ()
        
        self.face = face
        self.onData = onData
        self.onTimeout = onTimeout
        self.foundVersion = None

    def upcall(self, kind, upcallInfo):
        if (kind == UPCALL_CONTENT or
            kind == UPCALL_CONTENT_UNVERIFIED or
            kind == UPCALL_CONTENT_UNVERIFIED or
            kind == UPCALL_CONTENT_KEYMISSING or
            kind == UPCALL_CONTENT_RAW):
            self._foundVersion = upcallInfo.Data

            template = upcallInfo.Interest
            template.exclude = Interest.ExclusionFilter ()
            template.exclude.add_any ()

            name = upcallInfo.Data.name
            if len(upcallInfo.Interest.name) == len(name):
                 return self.onData (upcallInfo.Interest, self._foundVersion)

            comp = upcallInfo.Data.name[len(self._baseName)]
            template.exclude.add_name (Name.Name ().append (comp))

            self.face.expressInterest (upcallInfo.Interest.name, self, template)
            return RESULT_OK

        elif (kind == UPCALL_INTEREST_TIMED_OUT):
            if self._foundVersion:
                self.onData (upcallInfo.Interest, self._foundVersion)
            else:
                if self.onTimeout:
                    self.onTimeout (upcallInfo.Interest)
        return RESULT_OK

class TrivialFilterClosure (Closure):
    __slots__ = ["_baseName", "_onInterest"];

    def __init__ (self, baseName, onInterest):
        self._baseName = baseName
        self._onInterest = onInterest

    def upcall(self, kind, upcallInfo):
        if (kind == UPCALL_INTEREST):
            self._onInterest (self._baseName, upcallInfo.Interest)

        return RESULT_OK
