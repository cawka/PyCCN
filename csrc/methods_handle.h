/*
 * Copyright (c) 2011, Regents of the University of California
 * BSD license, See the COPYING file for more information
 * Written by: Derek Kulinski <takeda@takeda.tk>
 *             Jeff Burke <jburke@ucla.edu>
 */

#ifndef METHODS_HANDLE_H
#  define	METHODS_HANDLE_H

PyObject *_pyndn_cmd_create(PyObject *UNUSED(self), PyObject *UNUSED(args));
PyObject *_pyndn_cmd_connect(PyObject *UNUSED(self), PyObject *py_ndn_handle);
PyObject *_pyndn_cmd_disconnect(PyObject *UNUSED(self),
		PyObject *py_ndn_handle);
PyObject *_pyndn_cmd_defer_verification (PyObject *UNUSED(self), PyObject *args);
PyObject *_pyndn_get_connection_fd(PyObject *self, PyObject *py_handle);
PyObject *_pyndn_cmd_process_scheduled_operations(PyObject *self,
		PyObject *py_handle);
PyObject *_pyndn_cmd_output_is_pending(PyObject *self, PyObject *py_handle);
PyObject *_pyndn_cmd_is_run_executing(PyObject *self, PyObject *py_handle);
PyObject *_pyndn_cmd_run(PyObject *UNUSED(self), PyObject *args);
PyObject *_pyndn_cmd_set_run_timeout(PyObject *UNUSED(self), PyObject *args);
PyObject *_pyndn_cmd_express_interest(PyObject *UNUSED(self),
		PyObject *args);
PyObject *_pyndn_cmd_set_interest_filter(PyObject *UNUSED(self),
		PyObject *args);
PyObject *_pyndn_cmd_clear_interest_filter(PyObject *UNUSED(self), PyObject *args);
PyObject *_pyndn_cmd_get(PyObject *UNUSED(self), PyObject *args);
PyObject *_pyndn_cmd_put(PyObject *UNUSED(self), PyObject *args);
PyObject *_pyndn_cmd_get_default_key(PyObject *self, PyObject *arg);
PyObject *_pyndn_cmd_get_default_key_name(PyObject *self, PyObject *arg);

#endif	/* METHODS_HANDLE_H */
