/*
 * Copyright (c) 2011, Regents of the University of California
 * BSD license, See the COPYING file for more information
 * Written by: Derek Kulinski <takeda@takeda.tk>
 *             Jeff Burke <jburke@ucla.edu>
 */

#include "python_hdr.h"
#include <ndn/ndn.h>
#include <ndn/signing.h>

#include "pyndn.h"
#include "util.h"
#include "methods_contentobject.h"
#include "methods_interest.h"
#include "methods_key.h"
#include "methods_name.h"
#include "methods_signature.h"
#include "methods_signedinfo.h"
#include "objects.h"

static PyObject *
Content_from_ndn_parsed(struct ndn_charbuf *content_object,
		struct ndn_parsed_Data *parsed_content_object)
{
	const char *value;
	size_t size;
	PyObject *py_content;
	int r;

	r = ndn_content_get_value(content_object->buf, content_object->length,
			parsed_content_object, (const unsigned char **) &value, &size);
	if (r < 0) {
		PyErr_Format(g_PyExc_NDNError, "ndn_content_get_value() returned"
				" %d", r);
		return NULL;
	}

	py_content = PyBytes_FromStringAndSize(value, size);
	if (!py_content)
		return NULL;

	return py_content;
}

static PyObject *
Name_obj_from_ndn_parsed(PyObject *py_content_object)
{
	struct ndn_charbuf *content_object;
	struct ndn_parsed_Data *parsed_content_object;
	PyObject *py_ndn_name;
	PyObject *py_Name;
	struct ndn_charbuf *name;
	size_t name_begin, name_end, s;
	int r;

	assert(NDNObject_IsValid(CONTENT_OBJECT, py_content_object));

	content_object = NDNObject_Get(CONTENT_OBJECT, py_content_object);
	parsed_content_object = _pyndn_content_object_get_pco(py_content_object);
	if (!parsed_content_object)
		return NULL;

	name_begin = parsed_content_object->offset[NDN_PCO_B_Name];
	name_end = parsed_content_object->offset[NDN_PCO_E_Name];
	s = name_end - name_begin;

	debug("Data_from_ndn_parsed Name len=%zd\n", s);
	if (parsed_content_object->name_ncomps <= 0) {
		PyErr_SetString(g_PyExc_NDNNameError, "No name stored (or name is"
				" invalid) in parsed content object");
		return NULL;
	}

	py_ndn_name = NDNObject_New_charbuf(NAME, &name);
	if (!py_ndn_name)
		return NULL;

	r = ndn_charbuf_append(name, &content_object->buf[name_begin], s);
	if (r < 0) {
		Py_DECREF(py_ndn_name);
		return PyErr_NoMemory();
	}

#if DEBUG_MSG
	debug("Name: ");
	dump_charbuf(name, stderr);
	debug("\n");
#endif

	py_Name = Name_obj_from_ndn(py_ndn_name);
	Py_DECREF(py_ndn_name);

	return py_Name;
}

static int
parse_Data(PyObject *py_content_object)
{
	struct content_object_data *context;
	struct ndn_charbuf *content_object;
	int r;

	assert(NDNObject_IsValid(CONTENT_OBJECT, py_content_object));

	context = PyCapsule_GetContext(py_content_object);
	assert(context);
	if (context->pco)
		free(context->pco);
	ndn_indexbuf_destroy(&context->comps);

	/*
	 * no error happens between deallocation and following line, so I'm not
	 * setting context->pco to NULL
	 */
	context->pco = calloc(1, sizeof(struct ndn_parsed_Data));
	JUMP_IF_NULL_MEM(context->pco, error);

	context->comps = ndn_indexbuf_create();
	JUMP_IF_NULL_MEM(context->comps, error);

	content_object = NDNObject_Get(CONTENT_OBJECT, py_content_object);

	r = ndn_parse_Data(content_object->buf, content_object->length,
			context->pco, context->comps);
	if (r < 0) {
		PyErr_SetString(g_PyExc_NDNDataError, "Unable to parse the"
				" Data");
		goto error;
	}

	return 0;
error:
	if (context->pco) {
		free(context->pco);
		context->pco = NULL;
	}
	ndn_indexbuf_destroy(&context->comps);
	return -1;
}

struct ndn_parsed_Data *
_pyndn_content_object_get_pco(PyObject *py_content_object)
{
	struct content_object_data *context;
	int r;

	assert(NDNObject_IsValid(CONTENT_OBJECT, py_content_object));

	context = PyCapsule_GetContext(py_content_object);
	assert(context);

	if (context->pco)
		return context->pco;

	r = parse_Data(py_content_object);
	JUMP_IF_NEG(r, error);

	assert(context->pco);
	return context->pco;

error:
	return NULL;
}

void
_pyndn_content_object_set_pco(PyObject *py_content_object,
		struct ndn_parsed_Data *pco)
{
	struct content_object_data *context;

	assert(NDNObject_IsValid(CONTENT_OBJECT, py_content_object));

	context = PyCapsule_GetContext(py_content_object);
	assert(context);

	if (context->pco)
		free(context->pco);

	context->pco = pco;
}

struct ndn_indexbuf *
_pyndn_content_object_get_comps(PyObject *py_content_object)
{
	struct content_object_data *context;
	int r;

	assert(NDNObject_IsValid(CONTENT_OBJECT, py_content_object));

	context = PyCapsule_GetContext(py_content_object);
	assert(context);

	if (context->comps)
		return context->comps;

	r = parse_Data(py_content_object);
	JUMP_IF_NEG(r, error);

	assert(context->comps);
	return context->comps;

error:
	return NULL;
}

void
_pyndn_content_object_set_comps(PyObject *py_content_object,
		struct ndn_indexbuf *comps)
{
	struct content_object_data *context;

	assert(NDNObject_IsValid(CONTENT_OBJECT, py_content_object));

	context = PyCapsule_GetContext(py_content_object);
	assert(context);

	if (context->comps)
		free(context->comps);

	context->comps = comps;
}

// ** Methods of Data
//
// Content Objects

PyObject *
Data_obj_from_ndn_buffer (PyObject *py_buffer)
{
  int r;
  Py_buffer buffer;
  PyObject *py_o;
  PyObject *py_data = NULL;
  struct ndn_charbuf *data;

  if (!PyObject_CheckBuffer (py_buffer))
    {
      PyErr_SetString(PyExc_TypeError, "The argument is not a buffer");
      return NULL;
    }

  r = PyObject_GetBuffer (py_buffer, &buffer, PyBUF_SIMPLE);
  if (r < 0)
    {
      PyErr_SetString(PyExc_TypeError, "The argument is not a buffer");
      return NULL;
    }

  py_data = NDNObject_New_charbuf (CONTENT_OBJECT, &data);
  JUMP_IF_NULL(py_data, error);
  r = ndn_charbuf_append (data, buffer.buf, buffer.len);
  JUMP_IF_NEG_MEM(r, error);

  py_o = Data_obj_from_ndn (py_data);
  Py_CLEAR(py_data);
  JUMP_IF_NULL(py_o, error);

  return py_o;
  
error:
  return NULL;
}

PyObject *
Data_obj_from_ndn(PyObject *py_content_object)
{
	struct ndn_charbuf *content_object;
	struct ndn_parsed_Data *parsed_content_object;
	PyObject *py_obj_Data, *py_o;
	int r;
	struct ndn_charbuf *signature;
	PyObject *py_signature;
	struct ndn_charbuf *signed_info;
	PyObject *py_signed_info;

	if (!NDNObject_ReqType(CONTENT_OBJECT, py_content_object))
		return NULL;

	content_object = NDNObject_Get(CONTENT_OBJECT, py_content_object);
	parsed_content_object = _pyndn_content_object_get_pco(py_content_object);
	if (!parsed_content_object)
		return NULL;

	debug("Data_from_ndn_parsed content_object->length=%zd\n",
			content_object->length);

	py_obj_Data = PyObject_CallObject(g_type_Data, NULL);
	if (!py_obj_Data)
		return NULL;

	/* Name */
	py_o = Name_obj_from_ndn_parsed(py_content_object);
	JUMP_IF_NULL(py_o, error);
	r = PyObject_SetAttrString(py_obj_Data, "name", py_o);
	Py_DECREF(py_o);
	JUMP_IF_NEG(r, error);

	/* Content */
	py_o = Content_from_ndn_parsed(content_object, parsed_content_object);
	JUMP_IF_NULL(py_o, error);
	r = PyObject_SetAttrString(py_obj_Data, "content", py_o);
	Py_DECREF(py_o);
	JUMP_IF_NEG(r, error);

	/* Signature */
	debug("Data_from_ndn_parsed Signature\n");
	py_signature = NDNObject_New_charbuf(SIGNATURE, &signature);
	JUMP_IF_NULL(py_signature, error);
	r = ndn_charbuf_append(signature,
			&content_object->buf[parsed_content_object->offset[NDN_PCO_B_Signature]],
			(size_t) (parsed_content_object->offset[NDN_PCO_E_Signature]
			- parsed_content_object->offset[NDN_PCO_B_Signature]));
	if (r < 0) {
		PyErr_NoMemory();
		Py_DECREF(py_signature);
		goto error;
	}

	py_o = Signature_obj_from_ndn(py_signature);
	Py_DECREF(py_signature);
	JUMP_IF_NULL(py_o, error);
	r = PyObject_SetAttrString(py_obj_Data, "signature", py_o);
	Py_DECREF(py_o);
	JUMP_IF_NEG(r, error);

	debug("Data_from_ndn_parsed SignedInfo\n");

	py_signed_info = NDNObject_New_charbuf(SIGNED_INFO, &signed_info);
	JUMP_IF_NULL(py_signed_info, error);

	r = ndn_charbuf_append(signed_info,
			&content_object->buf[parsed_content_object->offset[NDN_PCO_B_SignedInfo]],
			(size_t) (parsed_content_object->offset[NDN_PCO_E_SignedInfo]
			- parsed_content_object->offset[NDN_PCO_B_SignedInfo]));
	if (r < 0) {
		PyErr_NoMemory();
		Py_DECREF(py_signed_info);
		goto error;
	}

	py_o = SignedInfo_obj_from_ndn(py_signed_info);
	Py_DECREF(py_signed_info);
	JUMP_IF_NULL(py_o, error);
	r = PyObject_SetAttrString(py_obj_Data, "signedInfo", py_o);
	Py_DECREF(py_o);
	JUMP_IF_NEG(r, error);

	debug("Data_from_ndn_parsed DigestAlgorithm\n");
	// TODO...  Note this seems to default to nothing in the library...?
	r = PyObject_SetAttrString(py_obj_Data, "digestAlgorithm", Py_None);
	JUMP_IF_NEG(r, error);

	/* Original data  */
	debug("Data_from_ndn_parsed ndn_data\n");
	r = PyObject_SetAttrString(py_obj_Data, "ndn_data", py_content_object);
	JUMP_IF_NEG(r, error);

	debug("Data_from_ndn_parsed complete\n");

	return py_obj_Data;

error:
	Py_XDECREF(py_obj_Data);
	return NULL;
}

PyObject *
_pyndn_cmd_content_to_bytearray(PyObject *UNUSED(self), PyObject *arg)
{
	PyObject *str, *result;

	if (arg == Py_None)
		Py_RETURN_NONE;
	else if (PyFloat_Check(arg) || PyLong_Check(arg) || _pyndn_Int_Check(arg)) {
		PyObject *py_o;

		py_o = PyObject_Str(arg);
		if (!py_o)
			return NULL;

#if PY_MAJOR_VERSION >= 3
		str = PyUnicode_EncodeUTF8(PyUnicode_AS_UNICODE(py_o),
				PyUnicode_GET_SIZE(py_o), NULL);
		Py_DECREF(py_o);
#else
		str = py_o;
#endif
	} else if (PyUnicode_Check(arg)) {
		str = PyUnicode_EncodeUTF8(PyUnicode_AS_UNICODE(arg),
				PyUnicode_GET_SIZE(arg), NULL);
	} else
		str = (Py_INCREF(arg), arg);

	if (!str)
		return NULL;

	result = PyByteArray_FromObject(str);
	Py_DECREF(str);

	return result;
}

PyObject *
_pyndn_cmd_content_to_bytes(PyObject *UNUSED(self), PyObject *arg)
{
	PyObject *str;

	if (arg == Py_None)
		Py_RETURN_NONE;
	else if (PyFloat_Check(arg) || PyLong_Check(arg) || _pyndn_Int_Check(arg)) {
		PyObject *py_o;

		py_o = PyObject_Str(arg);
		if (!py_o)
			return NULL;

#if PY_MAJOR_VERSION >= 3
		str = PyUnicode_EncodeUTF8(PyUnicode_AS_UNICODE(py_o),
				PyUnicode_GET_SIZE(py_o), NULL);
		Py_DECREF(py_o);
#else
		str = py_o;
#endif
		return str;
	} else if (PyUnicode_Check(arg))
		return PyUnicode_EncodeUTF8(PyUnicode_AS_UNICODE(arg),
			PyUnicode_GET_SIZE(arg), NULL);

	return PyObject_Bytes(arg);
}

PyObject *
_pyndn_cmd_encode_Data(PyObject *UNUSED(self), PyObject *args)
{
	PyObject *py_content_object, *py_name, *py_content, *py_signed_info,
			*py_key;
	PyObject *py_o = NULL, *ret = NULL;
	struct ndn_charbuf *name, *signed_info, *content_object = NULL;
	struct ndn_pkey *private_key;
	const char *digest_alg = NULL;
	char *content;
	Py_ssize_t content_len;
	int r;

	if (!PyArg_ParseTuple(args, "OOOOO", &py_content_object, &py_name,
			&py_content, &py_signed_info, &py_key))
		return NULL;

	if (strcmp(py_content_object->ob_type->tp_name, "Data")) {
		PyErr_SetString(PyExc_TypeError, "Must pass a Data as arg 1");
		return NULL;
	}

	if (!NDNObject_IsValid(NAME, py_name)) {
		PyErr_SetString(PyExc_TypeError, "Must pass a NDN Name as arg 2");
		return NULL;
	} else
		name = NDNObject_Get(NAME, py_name);

	if (py_content != Py_None && !PyBytes_Check(py_content)) {
		PyErr_SetString(PyExc_TypeError, "Must pass a Bytes as arg 3");
		return NULL;
	} else if (py_content == Py_None) {
		content = NULL;
		content_len = 0;
	} else {
		r = PyBytes_AsStringAndSize(py_content, &content, &content_len);
		if (r < 0)
			return NULL;
	}

	if (!NDNObject_IsValid(SIGNED_INFO, py_signed_info)) {
		PyErr_SetString(PyExc_TypeError, "Must pass a NDN SignedInfo as arg 4");
		return NULL;
	} else
		signed_info = NDNObject_Get(SIGNED_INFO, py_signed_info);

	if (strcmp(py_key->ob_type->tp_name, "Key")) {
		PyErr_SetString(PyExc_TypeError, "Must pass a Key as arg 4");
		return NULL;
	}

	// // DigestAlgorithm
	// py_o = PyObject_GetAttrString(py_content_object, "digestAlgorithm");
	// if (py_o != Py_None) {
	// 	PyErr_SetString(PyExc_NotImplementedError, "non-default digest"
	// 			" algorithm not yet supported");
	// 	goto error;
	// }
	// Py_CLEAR(py_o);

	// Key
	private_key = Key_to_ndn_private(py_key);
        
	// Note that we don't load this key into the keystore hashtable in the library
	// because it makes this method require access to a ndn handle, and in fact,
	// ndn_sign_content just uses what's in signedinfo (after an error check by
	// chk_signing_params and then calls ndn_encode_Data anyway
	//
	// Encode the content object

	// Build the Data here.
	content_object = ndn_charbuf_create();
	JUMP_IF_NULL_MEM(content_object, error);

	r = ndn_encode_ContentObject(content_object, name, signed_info, content,
			content_len, digest_alg, private_key);

	debug("ndn_encode_Data res=%d\n", r);
	if (r < 0) {
		ndn_charbuf_destroy(&content_object);
		PyErr_SetString(g_PyExc_NDNError, "Unable to encode Data");
		goto error;
	}

	ret = NDNObject_New(CONTENT_OBJECT, content_object);

error:
	Py_XDECREF(py_o);
	return ret;
}

PyObject *
_pyndn_cmd_Data_obj_from_ndn(PyObject *UNUSED(self), PyObject *py_co)
{
	return Data_obj_from_ndn(py_co);
}

PyObject *
_pyndn_cmd_Data_obj_from_ndn_buffer(PyObject *UNUSED(self), PyObject *py_buffer)
{
	return Data_obj_from_ndn_buffer(py_buffer);
}

PyObject *
_pyndn_cmd_digest_contentobject(PyObject *UNUSED(self), PyObject *args)
{
	PyObject *py_content_object;
	struct ndn_charbuf *content_object;
	struct ndn_parsed_Data *parsed_content_object;
	PyObject *py_digest;

	if (!PyArg_ParseTuple(args, "O", &py_content_object))
		return NULL;

	if (!NDNObject_IsValid(CONTENT_OBJECT, py_content_object)) {
		PyErr_SetString(PyExc_TypeError, "Expected NDN Data");
		return NULL;
	}

	content_object = NDNObject_Get(CONTENT_OBJECT, py_content_object);
	parsed_content_object = _pyndn_content_object_get_pco(py_content_object);
	if (!parsed_content_object)
		return NULL;

	/*
	 * sanity check (sigh, I guess pco and comps should be carried in
	 * capsule's context, since they're very closely related)
	 */
	if (content_object->length != parsed_content_object->offset[NDN_PCO_E]) {
		PyErr_SetString(PyExc_ValueError, "Data size doesn't match"
				" the size reported by pco");
		return NULL;
	}

	ndn_digest_ContentObject(content_object->buf, parsed_content_object);
	py_digest = PyBytes_FromStringAndSize(
			(char *) parsed_content_object->digest,
			parsed_content_object->digest_bytes);

	return py_digest;
}

PyObject *
_pyndn_cmd_content_matches_interest(PyObject *UNUSED(self), PyObject *args)
{
	PyObject *py_content_object, *py_interest;
	struct ndn_charbuf *content_object, *interest;
	struct ndn_parsed_Data *pco;
	struct ndn_parsed_interest *pi;
	int r;
	PyObject *res;

	if (!PyArg_ParseTuple(args, "OO", &py_content_object, &py_interest))
		return NULL;

	if (!NDNObject_IsValid(CONTENT_OBJECT, py_content_object)) {
		PyErr_SetString(PyExc_TypeError, "Expected NDN Data");
		return NULL;
	}

	if (!NDNObject_IsValid(INTEREST, py_interest)) {
		PyErr_SetString(PyExc_TypeError, "Expected NDN Interest");
		return NULL;
	}

	content_object = NDNObject_Get(CONTENT_OBJECT, py_content_object);
	interest = NDNObject_Get(INTEREST, py_interest);

	pco = _pyndn_content_object_get_pco(py_content_object);
	if (!pco)
		return NULL;

	pi = _pyndn_interest_get_pi(py_interest);
	if (!pi)
		return NULL;

	r = ndn_content_matches_interest(content_object->buf,
			content_object->length, 1, pco, interest->buf, interest->length,
			pi);

	res = r ? Py_True : Py_False;

	return Py_INCREF(res), res;
}

PyObject *
_pyndn_cmd_verify_content(PyObject *UNUSED(self), PyObject *args)
{
	PyObject *py_handle, *py_content_object;
	PyObject *res;
	struct ndn *handle;
	struct ndn_charbuf *content_object;
	struct ndn_parsed_Data *pco;
	int r;

	if (!PyArg_ParseTuple(args, "OO", &py_handle, &py_content_object))
		return NULL;

	if (!NDNObject_IsValid(HANDLE, py_handle)) {
		PyErr_SetString(PyExc_TypeError, "argument 1 must be a NDN handle");
		return NULL;
	}

	if (!NDNObject_IsValid(CONTENT_OBJECT, py_content_object)) {
		PyErr_SetString(PyExc_TypeError, "argument 2 must be NDN"
				" Data");
		return NULL;
	}


	handle = NDNObject_Get(HANDLE, py_handle);
	content_object = NDNObject_Get(CONTENT_OBJECT, py_content_object);
	pco = _pyndn_content_object_get_pco(py_content_object);
	if (!pco)
		return NULL;

	assert(content_object->length == pco->offset[NDN_PCO_E]);

	r = ndn_verify_content(handle, content_object->buf, pco);

	res = r == 0 ? Py_True : Py_False;

	return Py_INCREF(res), res;
}

PyObject *
_pyndn_cmd_verify_signature(PyObject *UNUSED(self), PyObject *args)
{
	PyObject *py_content_object, *py_pub_key;
	PyObject *res;
	struct ndn_charbuf *content_object;
	struct ndn_parsed_Data *pco;
	struct ndn_pkey *pub_key;
	int r;

	if (!PyArg_ParseTuple(args, "OO", &py_content_object, &py_pub_key))
		return NULL;

	if (!NDNObject_IsValid(CONTENT_OBJECT, py_content_object)) {
		PyErr_SetString(PyExc_TypeError, "argument 1 must be NDN"
				" Data");
		return NULL;
	}

	if (!NDNObject_IsValid(PKEY_PUB, py_pub_key)) {
		PyErr_SetString(PyExc_TypeError, "argument 2 must be NDN public key");
		return NULL;
	}

	content_object = NDNObject_Get(CONTENT_OBJECT, py_content_object);
	pco = _pyndn_content_object_get_pco(py_content_object);
	if (!pco)
		return NULL;

	pub_key = NDNObject_Get(PKEY_PUB, py_pub_key);

	r = ndn_verify_signature(content_object->buf, content_object->length, pco,
			pub_key);
	if (r < 0) {
		PyErr_SetString(g_PyExc_NDNSignatureError, "error verifying signature");
		return NULL;
	}

	res = r ? Py_True : Py_False;

	return Py_INCREF(res), res;
}
