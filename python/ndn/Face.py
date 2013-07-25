## -*- Mode: python; py-indent-offset: 4; indent-tabs-mode: nil; coding: utf-8; -*-
#
# Copyright (c) 2011-2013, Regents of the University of California
# BSD license, See the COPYING file for more information
# Written by: Derek Kulinski <takeda@takeda.tk>
#             Jeff Burke <jburke@ucla.edu>
#             Alexander Afanasyev <alexander.afanasyev@ucla.edu>
#

import _ndn

import Closure
import Interest
from Name import Name

import threading

class Face (object):
    """
    Class that provides interface to connect to the underlying NDN daemon
    """
    
    def __init__(self):
        self._handle_lock = threading.Lock()
        self.ccn_data = _ndn.create()
        self.connect ()

    def connect (self):
        _ndn.connect(self.ccn_data)

    def disconnect (self):
        _ndn.disconnect(self.ccn_data)

    def defer_verification (self, deferVerification = True):
        _ndn.defer_verification(self.ccn_data, 1 if deferVerification else 0)

    def _acquire_lock(self, tag):
        if not _ndn.is_run_executing(self.ccn_data):
            self._handle_lock.acquire()

    def _release_lock(self, tag):
        if not _ndn.is_run_executing(self.ccn_data):
            self._handle_lock.release()

    def fileno(self):
        return _ndn.get_connection_fd(self.ccn_data)

    def process_scheduled(self):
        assert not _ndn.is_run_executing(self.ccn_data), "Command should be called when ccn_run is not running"
        return _ndn.process_scheduled_operations(self.ccn_data)

    def output_is_pending(self):
        assert not _ndn.is_run_executing(self.ccn_data), "Command should be called when ccn_run is not running"
        return _ndn.output_is_pending(self.ccn_data)

    def run(self, timeoutms):
        assert not _ndn.is_run_executing(self.ccn_data), "Command should be called when ccn_run is not running"
        self._handle_lock.acquire()
        try:
            _ndn.run(self.ccn_data, timeoutms)
        finally:
            self._handle_lock.release()

    def setRunTimeout(self, timeoutms):
        _ndn.set_run_timeout(self.ccn_data, timeoutms)

    # Application-focused methods
    #
    def _expressInterest(self, name, closure, template = None):
        self._acquire_lock("expressInterest")
        try:
            return _ndn.express_interest(self, name, closure, template)
        finally:
            self._release_lock("expressInterest")

    def expressInterest (self, name, onData, onTimeout = None, template = None):
        if not isinstance (name, Name):
            name = Name (name)
        self._expressInterest (name, 
                               Closure.TrivialExpressClosure (onData, onTimeout), 
                               template)

    def expressInterestForLatest (self, name, onData, onTimeout = None, timeoutms = 1.0):
        if not isinstance (name, Name):
            name = Name (name)
        self.expressInterest (name,
                              Closure.VersionResolverClosure (self, onData, onTimeout), 
                              Interest.Interest (interestLifetime = timeoutms, 
                                                 childSelector = Interest.CHILD_SELECTOR_LEFT))

    def _setInterestFilter(self, name, closure, flags = None):
        self._acquire_lock("setInterestFilter")
        try:
            if flags is None:
                return _ndn.set_interest_filter(self.ccn_data, name.ccn_data, closure)
            else:
                return _ndn.set_interest_filter(self.ccn_data, name.ccn_data, closure, flags)
        finally:
            self._release_lock("setInterestFilter")

    def setInterestFilter (self, name, onInterest, flags = None):
        if not isinstance (name, Name):
            name = Name (name)

        self._setInterestFilter (name, 
                                 Closure.TrivialFilterClosure (name, onInterest), 
                                 flags)

    def clearInterestFilter(self, name):
        if not isinstance (name, Name):
            name = Name (name)

        self._acquire_lock("setInterestFilter")
        try:
            return _ndn.clear_interest_filter(self.ccn_data, name.ccn_data)
        finally:
            self._release_lock("setInterestFilter")

    # Blocking!
    def get (self, name, template = None, timeoutms = 3000):
        raise NotImplementedError ("Blocking get operation is deprecated. Use expressInterestSimple with appropriate callback instead")

        if not isinstance (name, Name):
            name = Name (name)
        self._acquire_lock("get")
        try:
            return _ndn.get(self, name, template, timeoutms)
        finally:
            self._release_lock("get")

    def put(self, contentObject):
        self._acquire_lock("put")
        try:
            return _ndn.put(self, contentObject)
        finally:
            self._release_lock("put")


