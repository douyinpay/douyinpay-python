# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

import os, sys, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from bytedance.douyinpay.callback import CallbackHandler, parse_callback, NotifyRequest
from bytedance.douyinpay.client import DouyinPayClient
from bytedance.douyinpay.config import DouYinPayConfig
from bytedance.douyinpay.constants import SignType, Headers
from bytedance.douyinpay.crypto.rsa import load_rsa_private_key, rsa_sign
from bytedance.douyinpay.crypto.aes import aes_encrypt
from bytedance.douyinpay.errors import DouYinPayError
from bytedance.douyinpay.factory import create_rsa_client
from bytedance.douyinpay.formatter import build_response_verify_message
from tests.helpers import CERT_PEM, MCH_PRIV, PLAT_SERIAL


AES_KEY = b"k" * 32


class StaticCertificateProvider:
    def __init__(self, certs):
        self._certs = certs

    def get_certs(self):
        return dict(self._certs)


def _make_callback(body: str, sign_priv_key=MCH_PRIV) -> dict:
    priv = load_rsa_private_key(sign_priv_key)
    ts = int(time.time())
    nonce = "cb-nonce"
    msg = build_response_verify_message(ts, nonce, body)
    sig = rsa_sign(msg, priv)
    return {
        Headers.Timestamp: str(ts),
        Headers.Nonce: nonce,
        Headers.Signature: sig,
        Headers.Serial: PLAT_SERIAL,
    }


def _make_encrypted_notify_body():
    biz = {"out_trade_no": "T001", "amount": 100}
    biz_str = json.dumps(biz)
    ct = aes_encrypt(biz_str, AES_KEY, b"n" * 12, aad="txn")
    notify = {
        "id": "evt-1",
        "create_time": "2024-01-01T00:00:00+08:00",
        "event_type": "PAYMENT.SUCCESS",
        "resource_type": "encrypt-resource",
        "resource": {
            "algorithm": "AEAD_AES_256_GCM",
            "ciphertext": ct,
            "nonce": "n" * 12,
            "associated_data": "txn",
        },
        "summary": "支付成功",
    }
    return json.dumps(notify, ensure_ascii=False), biz_str


def test_parse_callback_aes():
    body, biz_str = _make_encrypted_notify_body()
    headers = _make_callback(body)
    handler = CallbackHandler(
        encrypt_key=AES_KEY,
        certs={PLAT_SERIAL: CERT_PEM},
        sign_type=SignType.RSA,
    )
    result = handler.parse(headers, body)
    assert isinstance(result, NotifyRequest)
    assert result.id == "evt-1"
    assert result.event_type == "PAYMENT.SUCCESS"
    assert result.resource is not None
    assert result.resource.algorithm.startswith("AEAD")
    assert result.resource.plaintext == biz_str
    assert result.content["out_trade_no"] == "T001"


def test_callback_handler_from_client_uses_client_certs():
    body, _ = _make_encrypted_notify_body()
    headers = _make_callback(body)
    client = create_rsa_client(
        "mch-1",
        "MCH-SER-001",
        MCH_PRIV,
        CERT_PEM,
        encrypt_key=AES_KEY,
    )
    try:
        handler = CallbackHandler.from_client(client)
        result = handler.parse(headers, body)
        assert result.content["out_trade_no"] == "T001"
    finally:
        client.close()


def test_client_parse_callback_uses_client_config():
    body, _ = _make_encrypted_notify_body()
    headers = _make_callback(body)
    client = create_rsa_client(
        "mch-1",
        "MCH-SER-001",
        MCH_PRIV,
        CERT_PEM,
        encrypt_key=AES_KEY,
    )
    try:
        result = client.parse_callback(headers, body)
        assert result.content["amount"] == 100
    finally:
        client.close()


def test_parse_callback_accepts_client_option():
    body, _ = _make_encrypted_notify_body()
    headers = _make_callback(body)
    client = create_rsa_client(
        "mch-1",
        "MCH-SER-001",
        MCH_PRIV,
        CERT_PEM,
        encrypt_key=AES_KEY,
    )
    try:
        result = parse_callback(headers, body, client=client)
        assert result.event_type == "PAYMENT.SUCCESS"
    finally:
        client.close()


def test_client_parse_callback_uses_certificate_provider():
    body, _ = _make_encrypted_notify_body()
    headers = _make_callback(body)
    client = DouyinPayClient(DouYinPayConfig(
        mchid="mch-1",
        serial="MCH-SER-001",
        private_key=MCH_PRIV,
        certs={},
        certificate_provider=StaticCertificateProvider({PLAT_SERIAL: CERT_PEM}),
        encrypt_key=AES_KEY,
    ))
    try:
        result = client.parse_callback(headers, body)
        assert result.content["out_trade_no"] == "T001"
    finally:
        client.close()


def test_parse_callback_from_client_requires_encrypt_key():
    client = create_rsa_client(
        "mch-1",
        "MCH-SER-001",
        MCH_PRIV,
        CERT_PEM,
    )
    try:
        with pytest.raises(DouYinPayError, match="encrypt_key is required"):
            client.parse_callback({}, "{}")
    finally:
        client.close()


def test_parse_callback_verify_fails_without_cert():
    notify = {"resource": {"algorithm": "AES", "ciphertext": "AA==", "nonce": "n"}}
    body = json.dumps(notify)
    headers = _make_callback(body)
    with pytest.raises(Exception):
        parse_callback(headers, body, encrypt_key=AES_KEY, certs={})


def test_parse_callback_unsupported_algorithm():
    notify = {"resource": {"algorithm": "UNKNOWN-ALG", "ciphertext": "AA==", "nonce": "n"}}
    body = json.dumps(notify)
    headers = _make_callback(body)
    with pytest.raises(Exception):
        parse_callback(
            headers, body,
            encrypt_key=AES_KEY,
            certs={PLAT_SERIAL: CERT_PEM},
        )


class _OnDemandCertificateProvider:
    """初始无证书；refresh_for_serial 被调用时注入平台证书，模拟回调验签按需刷新。"""

    def __init__(self, certs_after_refresh):
        self._certs = {}
        self._certs_after_refresh = certs_after_refresh
        self.refreshed_serials = []

    def get_certs(self):
        return dict(self._certs)

    def refresh_for_serial(self, serial):
        self.refreshed_serials.append(serial)
        self._certs = dict(self._certs_after_refresh)
        return dict(self._certs)


def test_callback_verify_refreshes_on_unknown_serial():
    body, _ = _make_encrypted_notify_body()
    headers = _make_callback(body)
    provider = _OnDemandCertificateProvider({PLAT_SERIAL: CERT_PEM})
    handler = CallbackHandler(
        encrypt_key=AES_KEY,
        certs={},
        certificate_provider=provider,
        sign_type=SignType.RSA,
    )
    result = handler.parse(headers, body)
    assert provider.refreshed_serials == [PLAT_SERIAL]
    assert result.content["out_trade_no"] == "T001"
