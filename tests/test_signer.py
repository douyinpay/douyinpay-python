# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

import os, sys, time, base64
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')

import pytest
from bytedance.douyinpay.signer import sign_request, verify_response, create_signer
from bytedance.douyinpay.crypto.rsa import load_rsa_private_key, load_rsa_public_key, rsa_sign
from bytedance.douyinpay.constants import SignType, Headers, ERR_RES_HEADERS_INCOMPLETE
from bytedance.douyinpay.errors import DouYinPaySignatureError
from bytedance.douyinpay.utils.pem import get_certificate_serial_number
from bytedance.douyinpay.formatter import build_response_verify_message


PRIV_PATH = os.path.join(FIXTURES, "rsa_merchant_key.pem")
CERT_PATH = os.path.join(FIXTURES, "rsa_platform_cert.pem")


def test_create_signer():
    r = create_signer("RSA")
    assert r.sign_type == "RSA"
    s = create_signer("SM2")
    assert s.sign_type == "SM2"
    with pytest.raises(Exception):
        create_signer("INVALID")


def test_sign_request_rsa_produces_headers():
    priv = load_rsa_private_key(PRIV_PATH)
    signed = sign_request(
        "POST", "/v1/orders?x=1", '{"a":1}',
        "mch-1", "ser-1", priv, SignType.RSA,
    )
    assert Headers.Authorization in signed.headers
    assert signed.headers[Headers.Timestamp] == str(signed.timestamp)
    assert signed.headers[Headers.Nonce] == signed.nonce
    assert "DouyinPay-RSA" in signed.headers[Headers.Authorization]


def test_verify_response_rsa_passes():
    priv = load_rsa_private_key(PRIV_PATH)
    cert_pem = open(CERT_PATH, "rb").read()
    serial = get_certificate_serial_number(cert_pem)
    body = '{"ok":true}'
    ts = int(time.time())
    nonce = "abcdef"
    msg = build_response_verify_message(ts, nonce, body)
    sig = rsa_sign(msg, priv)
    headers = {
        Headers.Timestamp: str(ts),
        Headers.Nonce: nonce,
        Headers.Signature: sig,
        Headers.Serial: serial,
    }
    certs = {serial: cert_pem}
    verify_response(headers, body, certs, SignType.RSA)


def test_verify_response_missing_headers():
    with pytest.raises(DouYinPaySignatureError, match=ERR_RES_HEADERS_INCOMPLETE.split()[0]):
        verify_response({}, "", {"X": b""})


def test_verify_response_bad_serial():
    headers = {
        Headers.Timestamp: str(int(time.time())),
        Headers.Nonce: "n",
        Headers.Signature: "sig",
        Headers.Serial: "DOES-NOT-EXIST",
    }
    with pytest.raises(DouYinPaySignatureError):
        verify_response(headers, "", {"X": b""})


def test_verify_response_bad_signature():
    priv = load_rsa_private_key(PRIV_PATH)
    cert_pem = open(CERT_PATH, "rb").read()
    serial = get_certificate_serial_number(cert_pem)
    headers = {
        Headers.Timestamp: str(int(time.time())),
        Headers.Nonce: "n",
        Headers.Signature: base64.b64encode(b"BADSIG" * 32).decode(),
        Headers.Serial: serial,
    }
    with pytest.raises(DouYinPaySignatureError):
        verify_response(headers, "body", {serial: cert_pem}, SignType.RSA)
