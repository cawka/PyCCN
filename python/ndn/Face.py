#
# Copyright (c) 2011-2013, Regents of the University of California
# BSD license, See the COPYING file for more information
# Written by: Derek Kulinski <takeda@takeda.tk>
#             Jeff Burke <jburke@ucla.edu>
#             Alexander Afanasyev <alexander.afanasyev@ucla.edu>
#

from ndn import _ndn

import Closure
import Interest
import Name
import select, time
import threading
#import dummy_threading as threading

# Fronts ccn

# ccn_handle is opaque to c struct

class Face (object):
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
#			print("%s: acquiring lock" % tag)
			self._handle_lock.acquire()
#			print("%s: lock acquired" % tag)

	def _release_lock(self, tag):
		if not _ndn.is_run_executing(self.ccn_data):
#			print("%s: releasing lock" % tag)
			self._handle_lock.release()
#			print("%s: lock released" % tag)

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
                class TrivialExpressClosure (Closure.Closure):
                        __slots__ = ["_onData", "_onTimeout"];

                        def __init__ (self, baseName, onData, onTimeout):
                                self._onData = onData
                                self._onTimeout = onTimeout

                        def upcall(self, kind, upcallInfo):
                                if (kind == Closure.UPCALL_CONTENT or
                                    kind == Closure.UPCALL_CONTENT_UNVERIFIED or
                                    kind == Closure.UPCALL_CONTENT_UNVERIFIED or
                                    kind == Closure.UPCALL_CONTENT_KEYMISSING or
                                    kind == Closure.UPCALL_CONTENT_RAW):
                                        self._onData (upcallInfo.Interest, upcallInfo.ContentObject)
                                elif (kind == Closure.UPCALL_INTEREST_TIMED_OUT):
                                        if self._onTimeout:
                                                self._onTimeout (upcallInfo.Interest)

                                # Always return RESULT_OK
                                return Closure.RESULT_OK

                trivial_closure = TrivialExpressClosure (name, onData, onTimeout)
                self._expressInterest (name, trivial_closure, template)

        def expressInterestForLatest (self, name, onData, onTimeout = None, timeoutms = 1.0):
                this = self

                class VersionResolverClosure (Closure.Closure):
                        __slots__ = ["_onData", "_onTimeout"];

                        def __init__ (self, baseName, onData, onTimeout):
                                self._onData = onData
                                self._onTimeout = onTimeout
                                self._foundVersion = None

                        def upcall(self, kind, upcallInfo):
                                if (kind == Closure.UPCALL_CONTENT or
                                    kind == Closure.UPCALL_CONTENT_UNVERIFIED or
                                    kind == Closure.UPCALL_CONTENT_UNVERIFIED or
                                    kind == Closure.UPCALL_CONTENT_KEYMISSING or
                                    kind == Closure.UPCALL_CONTENT_RAW):
                                        self._foundVersion = upcallInfo.ContentObject

                                        template = upcallInfo.Interest
                                        template.exclude = Interest.ExclusionFilter ()
                                        template.exclude.add_any ()

                                        name = upcallInfo.ContentObject.name
                                        if len(upcallInfo.Interest.name) == len(name):
                                             return self._onData (upcallInfo.Interest, self._foundVersion)

                                        comp = upcallInfo.ContentObject.name[len(self._baseName)]
                                        template.exclude.add_name (Name.Name ().append (comp))

                                        this.expressInterest (upcallInfo.Interest.name, self, template)
                                        return Closure.RESULT_OK

                                elif (kind == Closure.UPCALL_INTEREST_TIMED_OUT):
                                        if self._foundVersion:
                                                self._onData (upcallInfo.Interest, self._foundVersion)
                                        else:
                                                if self._onTimeout:
                                                        self._onTimeout (upcallInfo.Interest)
                                return Closure.RESULT_OK

                trivial_closure = VersionResolverClosure (name, onData, onTimeout)
                template = Interest.Interest (interestLifetime = timeoutms, childSelector = Interest.CHILD_SELECTOR_LEFT)
                self.expressInterest (name, trivial_closure, template)

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
                class TrivialFilterClosure (Closure.Closure):
                        __slots__ = ["_baseName", "_onInterest"];

                        def __init__ (self, baseName, onInterest):
                                self._baseName = baseName
                                self._onInterest = onInterest

                        def upcall(self, kind, upcallInfo):
                                if (kind == Closure.UPCALL_INTEREST):
                                        self._onInterest (self._baseName, upcallInfo.Interest)

                                return Closure.RESULT_OK

                trivial_closure = TrivialFilterClosure (name, onInterest)
                self._setInterestFilter (name, trivial_closure, flags)

        def clearInterestFilter(self, name):
                self._acquire_lock("setInterestFilter")
		try:
                        return _ndn.clear_interest_filter(self.ccn_data, name.ccn_data)
		finally:
			self._release_lock("setInterestFilter")

	# Blocking!
	def get (self, name, template = None, timeoutms = 3000):
                raise NotImplementedError ("Blocking get operation is deprecated. Use expressInterestSimple with appropriate callback instead")

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

	@staticmethod
	def getDefaultKey():
		return _ndn.get_default_key()

class EventLoop(object):
	def __init__(self, *handles):
		self.running = False
		self.fds = {}
		for handle in handles:
			self.fds[handle.fileno()] = handle
                self.eventLock = threading.Lock ()
                self.events = []

        def execute (self, event):
                self.eventLock.acquire ()
                self.events.append (event)
                self.eventLock.release ()

	def run_scheduled(self):
		wait = {}
		for fd, handle in zip(self.fds.keys(), self.fds.values()):
			wait[fd] = handle.process_scheduled()
		return wait[sorted(wait, key=wait.get)[0]] / 1000.0

	#
	# version that uses poll (might not work on Mac)
	#
	#def run_once(self):
	#	fd_state = select.poll()
	#	for handle in self.fds.values():
	#		flags = select.POLLIN
	#		if (handle.output_is_pending()):
	#			flags |= select.POLLOUT
	#		fd_state.register(handle, flags)
	#
	#	timeout = min(self.run_scheduled(), 1.000)
	#
	#	res = fd_state.poll(timeout)
	#	for fd, event in res:
	#		self.fds[fd].run(0)

	def run_once(self):
		fd_read = self.fds.values()
		fd_write = []
		for handle in self.fds.values():
			if handle.output_is_pending():
				fd_write.append(handle)

		timeout = min(self.run_scheduled(), 1.000)

                res = select.select(fd_read, fd_write, [], timeout)

		handles = set(res[0]).union(res[1])
		for handle in handles:
			handle.run(0)

	def run(self):
		self.running = True
                while self.running:
                        try:
                                self.eventLock.acquire ()
                                for event in self.events:
                                        event ()
                                self.events = []
                                self.eventLock.release ()

                                self.run_once()
                        except select.error, e:
                                if e[0] == 4:
                                        continue
                                else:
                                        raise
                self.running = False

	def stop(self):
		self.running = False
                for fd, handle in zip(self.fds.keys(), self.fds.values()):
                        handle.disconnect ()
