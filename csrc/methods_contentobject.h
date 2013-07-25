/*
 * Copyright (c) 2011, Regents of the University of California
 * BSD license, See the COPYING file for more information
 * Written by: Derek Kulinski <takeda@takeda.tk>
 *             Jeff Burke <jburke@ucla.edu>
 */

#ifndef MEDHODS_CONTENTOBJECT_H
#  define	MEDHODS_CONTENTOBJECT_H

#define ccn_parsed_Data ccn_parsed_ContentObject
#define ccn_parse_Data ccn_parse_ContentObject

struct ccn_parsed_Data *_ndn_content_object_get_pco(
		PyObject *py_content_object);
void _ndn_content_object_set_pco(PyObject *py_content_object,
		struct ccn_parsed_Data *pco);
struct ccn_indexbuf *_ndn_content_object_get_comps(
		PyObject *py_content_object);
void _ndn_content_object_set_comps(PyObject *py_content_object,
		struct ccn_indexbuf *comps);
PyObject *Data_obj_from_ccn(PyObject *py_content_object);
PyObject *Data_obj_from_ccn_buffer (PyObject *py_buffer);

PyObject *_ndn_cmd_content_to_bytes(PyObject *self, PyObject *arg);
PyObject *_ndn_cmd_content_to_bytearray(PyObject *self, PyObject *arg);
PyObject *_ndn_cmd_encode_Data(PyObject *self, PyObject *args);
PyObject *_ndn_cmd_Data_obj_from_ccn(PyObject *self, PyObject *py_co);
PyObject *_ndn_cmd_Data_obj_from_ccn_buffer(PyObject *self, PyObject *py_co);
PyObject *_ndn_cmd_digest_contentobject(PyObject *self, PyObject *args);
PyObject *_ndn_cmd_content_matches_interest(PyObject *self, PyObject *args);
PyObject *_ndn_cmd_verify_content(PyObject *self, PyObject *args);
PyObject *_ndn_cmd_verify_signature(PyObject *self, PyObject *args);

#endif	/* MEDHODS_CONTENTOBJECT_H */

