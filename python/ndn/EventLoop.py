## -*- Mode: python; py-indent-offset: 4; indent-tabs-mode: nil; coding: utf-8; -*-
#
# Copyright (c) 2011-2013, Regents of the University of California
# BSD license, See the COPYING file for more information
# Written by: Derek Kulinski <takeda@takeda.tk>
#             Jeff Burke <jburke@ucla.edu>
#             Alexander Afanasyev <alexander.afanasyev@ucla.edu>
#

import _ndn

import select
import threading

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
    #    fd_state = select.poll()
    #    for handle in self.fds.values():
    #        flags = select.POLLIN
    #        if (handle.output_is_pending()):
    #            flags |= select.POLLOUT
    #        fd_state.register(handle, flags)
    #
    #    timeout = min(self.run_scheduled(), 1.000)
    #
    #    res = fd_state.poll(timeout)
    #    for fd, event in res:
    #        self.fds[fd].run(0)

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
