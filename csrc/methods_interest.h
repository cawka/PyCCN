/*
 * Copyright (c) 2011, Regents of the University of California
 * BSD license, See the COPYING file for more information
 * Written by: Derek Kulinski <takeda@takeda.tk>
 *             Jeff Burke <jburke@ucla.edu>
 */

#ifndef METHODS_INTERESTS_H
#  define	METHODS_INTERESTS_H

PyObject *Interest_obj_from_ccn(PyObject *py_interest);

PyObject *_pyccn_Interest_to_ccn(PyObject *UNUSED(self),
		PyObject *py_interest);
PyObject *_pyccn_Interest_from_ccn(PyObject *UNUSED(self), PyObject *args);
PyObject *_pyccn_ExclusionFilter_to_ccn(PyObject *UNUSED(self),
		PyObject* args);
PyObject *_pyccn_ExclusionFilter_from_ccn(PyObject *UNUSED(self),
		PyObject* args);

#endif	/* METHODS_INTERESTS_H */

