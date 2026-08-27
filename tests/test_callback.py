import os, sys, json, time, base64
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')

import pytest
from douyinpay.callback import CallbackHandler, parse_callback, NotifyRequest
from douyinpay.constants import SignType, Headers
from douyinpay.crypto.rsa import load_rsa_private_key, rsa_sign
from douyinpay.crypto.aes import aes_encrypt
from douyinpay.crypto.sm4 import sm4_encrypt
from douyinpay.utils.pem import get_certificate_serial_number
from douyinpay.formatter import build_response_verify_message


PRIV_PATH = os.path.join(FIXTURES, "rsa_merchant_key.pem")
CERT_PATH = os.path.join(FIXTURES, "rsa_platform_cert.pem")
CERT_PEM = open(CERT_PATH, "rb").read()
PLAT_SERIAL = get_certificate_serial_number(CERT_PATH)
AES_KEY = b"k" * 32
SM4_KEY = b"s" * 16


def _make_callback(body: str, sign_priv_path=PRIV_PATH) -> dict:
    priv = load_rsa_private_key(open(sign_priv_path, "rb").read())
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


def test_parse_callback_aes():
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
    body = json.dumps(notify, ensure_ascii=False)
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


def test_parse_callback_sm4_algorithm_detected():
    biz = {"trade_no": "T002"}
    biz_str = json.dumps(biz)
    iv = b"I" * 16
    ct = sm4_encrypt(biz_str, SM4_KEY, iv)
    notify = {
        "resource": {
            "algorithm": "SM4-CBC",
            "ciphertext": ct,
            "nonce": "I" * 16,
            "associated_data": "",
        },
    }
    body = json.dumps(notify)
    headers = _make_callback(body)
    result = parse_callback(
        headers, body,
        encrypt_key=SM4_KEY,
        certs={PLAT_SERIAL: CERT_PEM},
        sign_type=SignType.RSA,
    )
    assert result.content["trade_no"] == "T002"


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
