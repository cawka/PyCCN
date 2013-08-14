/*
 * Copyright (c) 2011, Regents of the University of California
 * BSD license, See the COPYING file for more information
 * Written by: Derek Kulinski <takeda@takeda.tk>
 *             Jeff Burke <jburke@ucla.edu>
 */

#include "python_hdr.h"

#include <ndn/ndn.h>
#include <ndn/digest.h>
#include <ndn/uri.h>
#include <ndn/signing.h>
#include <ndn/keystore.h>

// On MacOS X, need to have the latest version from MacPorts
// and add /opt/local/include as an include path
#include <openssl/rsa.h>
#include <openssl/pem.h>
#include <openssl/evp.h>
#include <openssl/sha.h>
#include <openssl/rand.h>
#include <openssl/ossl_typ.h>
#include <openssl/err.h>

#include <assert.h>

#include "key_utils.h"
#include "pyndn.h"
#include "objects.h"
#include "util.h"

static char g_seed_file[200];
static int g_seeded = 0;

static void
save_seed(void)
{
	assert(*g_seed_file);

	if (!g_seeded)
		return; /* so we won't pollute the seed file*/

	RAND_write_file(g_seed_file);
}

static void
seed_prng(void)
{
	const char *file;
	int res;

	if (*g_seed_file)
		file = g_seed_file;
	else
		file = RAND_file_name(g_seed_file, sizeof(g_seed_file));

	if (!file)
		panic("Unable to obtain name for random seed file.");

	if (RAND_load_file(file, -1)) {
		g_seeded = 1;

		/* for a good measure */
		RAND_load_file("/dev/random", 8);

		return;
	}

	/*
	 * This is a special case, I hope it won't be normally used
	 * please review if this is sufficient, I'm not using purely /dev/random
	 * because some computers don't have enough enthropy
	 */
	res = RAND_load_file("/dev/urandom", 2048);
	if (res < 2048)
		panic("Unable to gather seed, /dev/urandom not available?");

	res = RAND_load_file("/dev/random", 32);
	if (res < 32)
		panic("Unable to gather enough entropy, /dev/random not available?");

	g_seeded = 1;
}

static int
create_key_digest(const unsigned char *dkey, size_t dkey_size,
		unsigned char **o_key_digest, size_t *o_key_digest_size)
{
	struct ndn_digest *digest;
	unsigned char *key_digest = NULL;
	size_t key_digest_size;
	int r;

	assert(o_key_digest);
	assert(o_key_digest_size);

	digest = ndn_digest_create(NDN_DIGEST_SHA256);
	JUMP_IF_NULL(digest, error);

	ndn_digest_init(digest);
	key_digest_size = ndn_digest_size(digest);

	key_digest = malloc(key_digest_size);
	JUMP_IF_NULL(key_digest, error);

	r = ndn_digest_update(digest, dkey, dkey_size);
	JUMP_IF_NEG(r, error);

	r = ndn_digest_final(digest, key_digest, key_digest_size);
	JUMP_IF_NEG(r, error);

	ndn_digest_destroy(&digest);

	*o_key_digest = key_digest;
	*o_key_digest_size = key_digest_size;

	return 0;

error:
	PyErr_SetString(g_PyExc_NDNKeyError, "unable to generate key digest");
	if (key_digest)
		free(key_digest);
	ndn_digest_destroy(&digest);
	return -1;
}

void
initialize_crypto(void)
{
	/* needed so openssl's errors make sense to humans */
	ERR_load_crypto_strings();
}

int
create_public_key_digest(struct ndn_pkey *key,
		PyObject **py_public_key_digest, int *public_key_digest_len)
{
	unsigned int err;
	unsigned char *public_key_der = NULL;
	size_t der_len;
	unsigned char *key_digest;
	size_t key_digest_size;
	PyObject *py_digest = NULL;
	int r;

	assert(key);
	assert(py_public_key_digest);

	r = i2d_PUBKEY((EVP_PKEY *)key, &public_key_der);
	if (r < 0) {
		goto openssl_error;
	}
	der_len = r;

	r = create_key_digest(public_key_der, der_len, &key_digest,
			&key_digest_size);
	free(public_key_der);
	public_key_der = NULL;
	JUMP_IF_NEG(r, error);

	py_digest = PyBytes_FromStringAndSize((char *) key_digest, key_digest_size);
	JUMP_IF_NULL(py_digest, error);

	*py_public_key_digest = py_digest;
	if (public_key_digest_len)
		*public_key_digest_len = key_digest_size;

	return 0;

openssl_error:
	err = ERR_get_error();
	PyErr_Format(g_PyExc_NDNKeyError, "Unable to generate digest from the key:"
			" %s", ERR_reason_error_string(err));
error:
	if (public_key_der)
		free(public_key_der);
	return -1;
}

int
ndn_keypair(int public_only, struct ndn_pkey *private_key,
            PyObject **py_private_key_ndn, PyObject **py_public_key_ndn)
{
	struct ndn_pkey *public_key = NULL;
	struct ndn_pkey *private_key_copy = NULL;
	PyObject *py_private_key = NULL, *py_public_key = NULL;
	unsigned int err;
	int r;

	if (!public_only && py_private_key_ndn) {
                private_key_copy = (struct ndn_pkey *) EVP_PKEY_new();
                JUMP_IF_NULL(private_key_copy, openssl_error);

                py_private_key = NDNObject_New(PKEY_PRIV, private_key_copy);
		JUMP_IF_NULL(py_private_key, error);
                
                RSA *private_key_rsa = EVP_PKEY_get1_RSA ((EVP_PKEY *)private_key);
                JUMP_IF_NULL(private_key_rsa, openssl_error);
                
                RSA* private_key_rsa_copy = RSAPrivateKey_dup (private_key_rsa);
                JUMP_IF_NULL(private_key_rsa_copy, openssl_error);
                
		r = EVP_PKEY_set1_RSA((EVP_PKEY *) private_key_copy, private_key_rsa_copy);
		RSA_free(private_key_rsa_copy);
		JUMP_IF_NULL(r, error);
	}

	if (py_public_key_ndn) {
		public_key = (struct ndn_pkey *) EVP_PKEY_new();
		JUMP_IF_NULL(public_key, openssl_error);

		py_public_key = NDNObject_New(PKEY_PUB, public_key);
		JUMP_IF_NULL(py_public_key, error);

                RSA *private_key_rsa = EVP_PKEY_get1_RSA ((EVP_PKEY *)private_key);
                JUMP_IF_NULL(private_key_rsa, openssl_error);
                
                RSA* public_key_rsa = RSAPublicKey_dup (private_key_rsa);
                JUMP_IF_NULL(public_key_rsa, openssl_error);

		r = EVP_PKEY_set1_RSA((EVP_PKEY *) public_key, public_key_rsa);
		RSA_free(public_key_rsa);
		JUMP_IF_NULL(r, error);
	}

	if (py_private_key_ndn) {
		*py_private_key_ndn = public_only ? (Py_INCREF(Py_None), Py_None) :
				py_private_key;
	}

	if (py_public_key_ndn)
		*py_public_key_ndn = py_public_key;

	return 0;

openssl_error:
	err = ERR_get_error();
	PyErr_Format(g_PyExc_NDNKeyError, "Unable to generate keypair from the key:"
			" %s", ERR_reason_error_string(err));
error:
	if (!py_public_key && public_key)
		ndn_pubkey_free(public_key);
	Py_XDECREF(py_public_key);
	Py_XDECREF(py_private_key);
	return -1;
}

PyObject *
_pyndn_privatekey_dup(const struct ndn_pkey *key)
{
	RSA *private_key_rsa;
	PyObject *py_private_key = NULL;
	struct ndn_pkey *private_key;
	unsigned int err;
	int r;

	private_key = (struct ndn_pkey *) EVP_PKEY_new();
	JUMP_IF_NULL(private_key, openssl_error);

	py_private_key = NDNObject_New(PKEY_PRIV, private_key);
	if (!py_private_key) {
		EVP_PKEY_free((EVP_PKEY *) private_key);
		goto error;
	}

	private_key_rsa = EVP_PKEY_get1_RSA((EVP_PKEY *) key);
	JUMP_IF_NULL(private_key_rsa, openssl_error);

	r = EVP_PKEY_set1_RSA((EVP_PKEY*) private_key, private_key_rsa);
	RSA_free(private_key_rsa);
	JUMP_IF_NEG(r, openssl_error);

	return py_private_key;

openssl_error:
	err = ERR_get_error();
	PyErr_Format(g_PyExc_NDNKeyError, "Unable to generate keypair from the key:"
			" %s", ERR_reason_error_string(err));
error:
	Py_XDECREF(py_private_key);
	return NULL;
}

//
// Caller must free
//

int
generate_key(int length, PyObject **py_private_key_ndn,
             PyObject **py_public_key_ndn, PyObject **py_public_key_digest,
             int *public_key_digest_len)
{
	RSA *private_key_rsa;
        struct ndn_pkey *private_key = NULL;
	int r;

	seed_prng();
	private_key_rsa = RSA_generate_key(length, 65537, NULL, NULL);
        private_key = (struct ndn_pkey *)EVP_PKEY_new();
        EVP_PKEY_assign_RSA ((EVP_PKEY *)private_key, private_key_rsa);
	save_seed ();

	if (!private_key_rsa || !private_key) {
		unsigned int err;

		err = ERR_get_error();
		PyErr_Format(g_PyExc_NDNKeyError, "Unable to generate the"
                             " key: %s", ERR_reason_error_string(err));
		return -1;
	}

	r = ndn_keypair(0, private_key, py_private_key_ndn,
                        py_public_key_ndn);
	if (r < 0)
		return -1;

	r = create_public_key_digest(private_key, py_public_key_digest,
                                     public_key_digest_len);
	if (r < 0)
		return -1;

        EVP_PKEY_free ((EVP_PKEY*)private_key);
        
	return 0;
}

//
// Writes without encryption/password!
//

int
write_key_pem_private(FILE *fp, struct ndn_pkey *private_key_ndn)
{
	unsigned long err;

	if (!PEM_write_PrivateKey(fp, (EVP_PKEY *) private_key_ndn, NULL, NULL, 0, NULL, NULL)) {
		err = ERR_get_error();
		PyErr_Format(g_PyExc_NDNKeyError, "Unable to write Private Key: %s",
				ERR_reason_error_string(err));
		return -1;
	}

	return 0;
}

int
write_key_pem_public(FILE *fp, struct ndn_pkey *public_key_ndn)
{
	unsigned long err;

	if (!PEM_write_PUBKEY(fp, (EVP_PKEY*) public_key_ndn)) {
		err = ERR_get_error();
		PyErr_Format(g_PyExc_NDNKeyError, "Unable to write Public Key: %s",
				ERR_reason_error_string(err));
		return -1;
	}

	return 0;
}

PyObject *
get_key_pem_private(const struct ndn_pkey *private_key_ndn)
{
	unsigned long err;
	BIO *bio;
	BUF_MEM *bufmem;
	int r;
	PyObject *py_res;

	bio = BIO_new(BIO_s_mem());
	JUMP_IF_NULL(bio, openssl_error);

	r = PEM_write_bio_PrivateKey(bio, (EVP_PKEY *) private_key_ndn, NULL, NULL, 0, NULL,
			NULL);
	if (!r)
		goto openssl_error;

	BIO_get_mem_ptr(bio, &bufmem);
	py_res = PyBytes_FromStringAndSize(bufmem->data, bufmem->length);
	r = BIO_free(bio);
	if (!r)
		goto openssl_error;

	return py_res;

openssl_error:
	err = ERR_get_error();
	PyErr_Format(g_PyExc_NDNKeyError, "Unable to obtain PEM: %s",
			ERR_reason_error_string(err));
	BIO_free(bio);
	return NULL;
}

PyObject *
get_key_pem_public(const struct ndn_pkey *key_ndn)
{
	unsigned long err;
	BIO *bio;
	BUF_MEM *bufmem;
	int r;
	PyObject *py_res;

	bio = BIO_new(BIO_s_mem());
	JUMP_IF_NULL(bio, openssl_error);

        r = PEM_write_bio_PUBKEY(bio, (EVP_PKEY *) key_ndn);
	if (!r)
		goto openssl_error;

	BIO_get_mem_ptr(bio, &bufmem);
	py_res = PyBytes_FromStringAndSize(bufmem->data, bufmem->length);
	r = BIO_free(bio);
	if (!r)
		goto openssl_error;

	return py_res;

openssl_error:
	err = ERR_get_error();
	PyErr_Format(g_PyExc_NDNKeyError, "Unable to obtain PEM: %s",
			ERR_reason_error_string(err));
	BIO_free(bio);
	return NULL;
}

PyObject *
get_key_der_private(struct ndn_pkey *private_key_ndn)
{
	PyObject *result;
	unsigned long err;
	unsigned char *private_key_der = NULL;
	int der_len;

	assert(private_key_ndn);

	der_len = i2d_PrivateKey((EVP_PKEY *) private_key_ndn, &private_key_der);
	JUMP_IF_NEG(der_len, openssl_error);

	result = PyBytes_FromStringAndSize((char *) private_key_der, der_len);
	JUMP_IF_NULL(result, error);

	return result;

openssl_error:
	err = ERR_get_error();
	PyErr_Format(g_PyExc_NDNKeyError, "Unable to write Private Key: %s",
			ERR_reason_error_string(err));
error:
	return NULL;
}

PyObject *
get_key_der_public(struct ndn_pkey *public_key_ndn)
{
	PyObject *result;
	unsigned long err;
	unsigned char *public_key_der = NULL;
	int der_len;

	der_len = i2d_PUBKEY((EVP_PKEY *) public_key_ndn, &public_key_der);
	JUMP_IF_NEG(der_len, openssl_error);

	result = PyBytes_FromStringAndSize((char *) public_key_der, der_len);
	JUMP_IF_NULL(result, error);

	return result;

openssl_error:
	err = ERR_get_error();
	PyErr_Format(g_PyExc_NDNKeyError, "Unable to write Public Key: %s",
			ERR_reason_error_string(err));
error:
	return NULL;
}

//
// Reads without decryption
//

int
read_key_pem(FILE *fp, PyObject **py_private_key_ndn,
		PyObject **py_public_key_ndn, PyObject **py_public_key_digest,
		int *public_key_digest_len)
{
        struct ndn_pkey *private_key = NULL;
	PyObject *py_private_key = NULL, *py_public_key = NULL;
	unsigned long err, reason;
	fpos_t fpos;
	int r;
	int public_only;

	r = fgetpos(fp, &fpos);
	JUMP_IF_NEG(r, errno_error);

	private_key = (struct ndn_pkey *)PEM_read_PrivateKey(fp, NULL, NULL, NULL);
	if (private_key) {
		public_only = 0;
		goto success;
	}

	err = ERR_get_error();
	reason = ERR_GET_REASON(err);

	/* 108 was meaning that start line isn't recognized */
	if (reason == 108) {
		r = fsetpos(fp, &fpos);
		JUMP_IF_NEG(r, errno_error);

		private_key = (struct ndn_pkey *)PEM_read_PUBKEY (fp, NULL, NULL, NULL);
		if (private_key) {
			public_only = 1;
			goto success;
		}

		err = ERR_get_error();
		reason = ERR_GET_REASON(err);
	}

	{
		char buf[256];

		ERR_error_string_n(err, buf, sizeof(buf));
		PyErr_Format(g_PyExc_NDNKeyError, "Unable to read Private Key: %s",
				buf);
		goto error;
	}

success:

	r = ndn_keypair(public_only, private_key, py_private_key_ndn,
			py_public_key_ndn);
	JUMP_IF_NEG(r, error);

	r = create_public_key_digest(private_key, py_public_key_digest,
			public_key_digest_len);
	JUMP_IF_NEG(r, error);

	return 0;

errno_error:
	PyErr_SetFromErrno(PyExc_IOError);
error:
	Py_XDECREF(py_private_key);
	Py_XDECREF(py_public_key);
	if (private_key)
		EVP_PKEY_free((EVP_PKEY *)private_key);
	return -1;
}

int
put_key_pem(int is_public_only, PyObject *py_key_pem,
            PyObject **py_private_key_ndn, PyObject **py_public_key_ndn,
            PyObject **py_public_key_digest)
{
	unsigned char *key_pem;
	Py_ssize_t pem_len;
	struct ndn_pkey *key = NULL;
	BIO *bio = NULL;
	int r;
	unsigned long err;

	r = PyBytes_AsStringAndSize(py_key_pem, (char **) &key_pem, &pem_len);
	JUMP_IF_NEG(r, error);

	bio = BIO_new_mem_buf(key_pem, pem_len);
	JUMP_IF_NULL(bio, openssl_error);

	if (is_public_only)
          key = (struct ndn_pkey*)PEM_read_bio_PUBKEY(bio, NULL, NULL, NULL);
	else
          key = (struct ndn_pkey*)PEM_read_bio_PrivateKey(bio, NULL, NULL, NULL);
	JUMP_IF_NULL(key, openssl_error);

	r = ndn_keypair(is_public_only, key, py_private_key_ndn, py_public_key_ndn);
	JUMP_IF_NEG(r, error);

	r = create_public_key_digest(key, py_public_key_digest, NULL);
	JUMP_IF_NEG(r, error);

	return 0;

openssl_error:
	err = ERR_get_error();
	PyErr_Format(g_PyExc_NDNKeyError, "Unable to parse key: %s",
			ERR_reason_error_string(err));
error:
	EVP_PKEY_free ((EVP_PKEY *)key);
	BIO_free(bio);
	return -1;
}

int
put_key_der(int is_public_only, PyObject *py_key_der,
            PyObject **py_private_key_ndn, PyObject **py_public_key_ndn,
            PyObject **py_public_key_digest, int *public_key_digest_len)
{
	struct ndn_pkey *key = NULL;
	const unsigned char *key_der;
	Py_ssize_t der_len;
	int r;
	unsigned long err;

	r = PyBytes_AsStringAndSize(py_key_der, (char **) &key_der, &der_len);
	JUMP_IF_NEG(r, error);

	if (is_public_only)
          key = (struct ndn_pkey*)d2i_PUBKEY(NULL, &key_der, der_len);
	else
          key = (struct ndn_pkey*)d2i_PrivateKey(EVP_PKEY_RSA, NULL, &key_der, der_len);

	r = ndn_keypair(is_public_only, key, py_private_key_ndn, py_public_key_ndn);
	JUMP_IF_NEG(r, error);

	r = create_public_key_digest(key, py_public_key_digest, public_key_digest_len);
	JUMP_IF_NEG(r, error);

	return 0;
error:
	return -1;
}

int
release_key(struct ndn_pkey** private_key_ndn, struct ndn_pkey** public_key_ndn, unsigned char** public_key_digest)
{
	if (public_key_ndn && *public_key_ndn)
		EVP_PKEY_free((EVP_PKEY*) * public_key_ndn);
	if (private_key_ndn && *private_key_ndn)
		EVP_PKEY_free((EVP_PKEY*) * private_key_ndn);
	if (public_key_digest && *public_key_digest)
		free(*public_key_digest);
	return 0;
}

int
release_keypair(struct keypair** KP)
{
	if (KP && *KP)
		free(*KP);
	return 0;
}

int
build_keylocator_from_key(struct ndn_charbuf** keylocator, struct ndn_pkey* key)
{
	int res = 0;

	*keylocator = ndn_charbuf_create();

	ndn_charbuf_append_tt(*keylocator, NDN_DTAG_KeyLocator, NDN_DTAG);
	ndn_charbuf_append_tt(*keylocator, NDN_DTAG_Key, NDN_DTAG);

	res = ndn_append_pubkey_blob(*keylocator, key);

	ndn_charbuf_append_closer(*keylocator); /* </Key> */
	ndn_charbuf_append_closer(*keylocator); /* </KeyLocator> */

	return(res);
}

int
get_ASN_public_key(unsigned char** public_key_der, int* public_key_der_len, struct ndn_pkey* private_key)
{
	unsigned char *pub;
	*public_key_der_len = i2d_PUBKEY((EVP_PKEY*)private_key, 0);
	*public_key_der = pub = (unsigned char*) calloc(*public_key_der_len, 1);
	i2d_PUBKEY((EVP_PKEY*)private_key, &pub);
	return 0;
}

RSA *
ndn_key_to_rsa(struct ndn_pkey *key_ndn)
{
	RSA *private_key_rsa;
	unsigned int err;

	private_key_rsa = EVP_PKEY_get1_RSA((EVP_PKEY *) key_ndn);
	if (!private_key_rsa) {
		err = ERR_get_error();
		PyErr_Format(g_PyExc_NDNKeyError, "Error obtaining private key: %s",
				ERR_reason_error_string(err));
		return NULL;
	}

	return private_key_rsa;
}
