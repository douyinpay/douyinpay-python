# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')

import pytest
import httpx
from bytedance.douyinpay.config import DouYinPayConfig
from bytedance.douyinpay.constants import SignType, EncryptType, GET_PLATFORM_CERTS_PATH, Headers
from bytedance.douyinpay.certificates import AutoCertificateManager, download_platform_certificates
from bytedance.douyinpay.crypto.aes import aes_encrypt
from bytedance.douyinpay.crypto.sm4 import sm4_encrypt
from bytedance.douyinpay.utils.pem import get_certificate_serial_number
from bytedance.douyinpay.crypto.rsa import load_rsa_private_key, rsa_sign
from bytedance.douyinpay.formatter import build_response_verify_message


PRIV_PATH = os.path.join(FIXTURES, "rsa_merchant_key.pem")
CERT_PATH = os.path.join(FIXTURES, "rsa_platform_cert.pem")
CERT_PEM_STR = open(CERT_PATH, "r").read()
PLAT_SERIAL = get_certificate_serial_number(CERT_PATH)
AES_KEY = b"a" * 32
SM4_KEY = b"s" * 16
MCH_PRIV = open(PRIV_PATH, "rb").read()


def _make_resp_factory(cipher_text, algo, cert_no=PLAT_SERIAL, status=200, nonce=None, aad="cert"):
    if nonce is None:
        nonce = "0123456789ab" if "AES" in algo else "IVV" * 5 + "1"

    def _handler(request):
        resp_body_dict = {
            "certificates": [
                {
                    "cert_no": cert_no,
                    "effective_time": "2024-01-01T00:00:00Z",
                    "expire_time": "2034-01-01T00:00:00Z",
                    "encrypt_certificate": {
                        "algorithm": algo,
                        "cipher_text": cipher_text,
                        "nonce": nonce,
                        "associated_data": aad,
                    },
                }
            ]
        }
        import json
        body = json.dumps(resp_body_dict)
        priv = load_rsa_private_key(MCH_PRIV)
        ts = int(time.time())
        nonce_str = "cert-n"
        msg = build_response_verify_message(ts, nonce_str, body)
        sig = rsa_sign(msg, priv)
        return httpx.Response(
            status,
            headers={
                Headers.Timestamp: str(ts),
                Headers.Nonce: nonce_str,
                Headers.Signature: sig,
                Headers.Serial: PLAT_SERIAL,
            },
            content=body,
        )
    return _handler


def test_download_platform_certificates_aes(httpx_mock):
    ct = aes_encrypt(CERT_PEM_STR, AES_KEY, b"0123456789ab", aad="cert")
    httpx_mock.add_callback(_make_resp_factory(ct, "AEAD_AES_256_GCM"))
    cfg = DouYinPayConfig(
        mchid="mch1", serial="mch-s",
        private_key=MCH_PRIV, certs={"_bootstrap": ""},
        sign_type=SignType.RSA, encrypt_type=EncryptType.AES,
        encrypt_key=AES_KEY,
    )
    downloaded = download_platform_certificates(cfg, verify_response=False)
    assert len(downloaded) == 1
    assert downloaded[0].serial_no == PLAT_SERIAL
    assert "BEGIN CERTIFICATE" in downloaded[0].certificate


def test_download_platform_certificates_sm4(httpx_mock):
    iv = "0123456789ABCDEF"
    ct = sm4_encrypt(CERT_PEM_STR, SM4_KEY, iv, aad="cert")
    httpx_mock.add_callback(_make_resp_factory(ct, "SM4-CBC", nonce=iv))
    cfg = DouYinPayConfig(
        mchid="mch1", serial="mch-s",
        private_key=MCH_PRIV, certs={"_bootstrap": ""},
        sign_type=SignType.SM2, encrypt_type=EncryptType.SM4,
        encrypt_key=SM4_KEY,
    )
    downloaded = download_platform_certificates(cfg, verify_response=False)
    assert len(downloaded) == 1
    assert "BEGIN CERTIFICATE" in downloaded[0].certificate


def test_auto_manager_ensure_ready_and_refresh(httpx_mock):
    ct = aes_encrypt(CERT_PEM_STR, AES_KEY, b"0123456789ab", aad="cert")
    httpx_mock.add_callback(_make_resp_factory(ct, "AEAD_AES_256_GCM"))
    mgr = AutoCertificateManager(
        mchid="mch1", serial="mch-s",
        private_key=MCH_PRIV, encrypt_key=AES_KEY,
        sign_type=SignType.RSA, encrypt_type=EncryptType.AES,
        refresh_interval_sec=3600,
    )
    try:
        certs = mgr.ensure_ready()
        assert len(certs) >= 1
        got = False
        for k, v in certs.items():
            if isinstance(v, bytes):
                if b"BEGIN CERTIFICATE" in v:
                    got = True
            else:
                if "BEGIN CERTIFICATE" in v:
                    got = True
        assert got
    finally:
        mgr.stop()


def test_auto_manager_start_stop(httpx_mock):
    ct = aes_encrypt(CERT_PEM_STR, AES_KEY, b"0123456789ab", aad="cert")
    httpx_mock.add_callback(_make_resp_factory(ct, "AEAD_AES_256_GCM"))
    mgr = AutoCertificateManager(
        mchid="mch1", serial="mch-s",
        private_key=MCH_PRIV, encrypt_key=AES_KEY,
        sign_type=SignType.RSA, encrypt_type=EncryptType.AES,
        refresh_interval_sec=1,
    )
    mgr.ensure_ready()
    mgr.start()
    time.sleep(0.05)
    mgr.stop()
    assert True


def test_auto_manager_timer_refresh_updates_cached_certs(httpx_mock):
    ct = aes_encrypt(CERT_PEM_STR, AES_KEY, b"0123456789ab", aad="cert")
    httpx_mock.add_callback(_make_resp_factory(ct, "AEAD_AES_256_GCM", cert_no="SERIAL_INITIAL"))
    httpx_mock.add_callback(_make_resp_factory(ct, "AEAD_AES_256_GCM", cert_no="SERIAL_UPDATED"))
    mgr = AutoCertificateManager(
        mchid="mch1", serial="mch-s",
        private_key=MCH_PRIV, encrypt_key=AES_KEY,
        sign_type=SignType.RSA, encrypt_type=EncryptType.AES,
        refresh_interval_sec=0.05,
    )
    try:
        certs = mgr.ensure_ready()
        assert "SERIAL_INITIAL" in certs
        mgr.start()
        for _ in range(50):
            if "SERIAL_UPDATED" in mgr.get_certs():
                break
            time.sleep(0.02)
        assert "SERIAL_UPDATED" in mgr.get_certs()
    finally:
        mgr.stop()


def test_auto_manager_start_with_zero_interval_does_not_schedule(httpx_mock):
    mgr = AutoCertificateManager(
        mchid="mch1", serial="mch-s",
        private_key=MCH_PRIV, encrypt_key=AES_KEY,
        sign_type=SignType.RSA, encrypt_type=EncryptType.AES,
        refresh_interval_sec=0,
    )
    mgr.start()
    try:
        assert mgr._timer is None
    finally:
        mgr.stop()


def test_auto_manager_concurrent_refresh_dedup(httpx_mock):
    call_count = [0]
    ct = aes_encrypt(CERT_PEM_STR, AES_KEY, b"0123456789ab", aad="cert")

    def handler(request):
        call_count[0] += 1
        time.sleep(0.1)
        return _make_resp_factory(ct, "AEAD_AES_256_GCM")(request)

    for _ in range(2):
        httpx_mock.add_callback(handler)
    mgr = AutoCertificateManager(
        mchid="mch1", serial="mch-s",
        private_key=MCH_PRIV, encrypt_key=AES_KEY,
        sign_type=SignType.RSA, encrypt_type=EncryptType.AES,
        refresh_interval_sec=3600,
    )
    try:
        mgr.ensure_ready()
        import threading
        barrier = threading.Barrier(2, timeout=5)

        def go():
            barrier.wait(timeout=2)
            mgr.refresh(True)

        t1 = threading.Thread(target=go)
        t2 = threading.Thread(target=go)
        t1.start(); t2.start()
        t1.join(); t2.join()
        # bootstrap（1次） + refresh并发去重（最多1次）
        assert 1 <= call_count[0] <= 2
    finally:
        mgr.stop()
