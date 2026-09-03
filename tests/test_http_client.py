# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')

import pytest
import httpx
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa as crypto_rsa
from cryptography.x509.oid import NameOID
from bytedance.douyinpay.config import DouYinPayConfig
from bytedance.douyinpay.constants import SignType, EncryptType, Headers, SdkAgentType
from bytedance.douyinpay.version import USER_AGENT, build_sdk_agent
from bytedance.douyinpay.http_client import HttpClient
from bytedance.douyinpay.factory import create_rsa_client
from bytedance.douyinpay.crypto.rsa import load_rsa_private_key, load_rsa_public_key, rsa_sign, rsa_verify
from bytedance.douyinpay.utils.pem import get_certificate_serial_number
from bytedance.douyinpay.utils.http import request_target_from_url
from bytedance.douyinpay.formatter import build_request_sign_message, build_response_verify_message


PRIV_PATH = os.path.join(FIXTURES, "rsa_merchant_key.pem")
CERT_PATH = os.path.join(FIXTURES, "rsa_platform_cert.pem")
CERT_PEM = open(CERT_PATH, "rb").read()
PLAT_SERIAL = get_certificate_serial_number(CERT_PATH)
MCHID = "mch-test"
MCH_SERIAL = "MCH-SER-001"

BASE_CONF = dict(
    mchid=MCHID,
    serial=MCH_SERIAL,
    private_key=open(PRIV_PATH, "rb").read(),
    certs={PLAT_SERIAL: CERT_PEM},
    sign_type=SignType.RSA,
    encrypt_type=EncryptType.AES,
    sdk_agent=SdkAgentType.RSA,
    base_url="https://api.test.local",
)


def _make_client(transport=None, **extra):
    cfg = DouYinPayConfig(**{**BASE_CONF, **extra})
    http_client = httpx.Client(transport=transport)
    cfg.http_client = http_client
    return HttpClient(cfg), http_client


def _make_rsa_key_and_cert(common_name: str):
    key = crypto_rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow() - timedelta(minutes=1))
        .not_valid_after(datetime.utcnow() + timedelta(days=365))
        .sign(key, hashes.SHA256())
    )
    key_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    return key_pem, cert_pem


def _parse_authorization_header(value):
    prefix = "DouyinPay-RSA "
    assert value.startswith(prefix)
    result = {}
    for item in value[len(prefix):].split(","):
        key, raw_value = item.split("=", 1)
        result[key.strip()] = raw_value.strip().strip('"')
    return result


def test_authorization_header(httpx_mock):
    import time as _time

    captured = {}

    def handler(request):
        captured["auth"] = request.headers.get(Headers.Authorization)
        captured["ua"] = request.headers.get(Headers.UserAgent)
        captured["agent"] = request.headers.get(Headers.SdkAgent)
        captured["timestamp"] = request.headers.get(Headers.Timestamp)
        captured["nonce"] = request.headers.get(Headers.Nonce)
        resp_body = '{"ok":1}'
        priv = load_rsa_private_key(open(PRIV_PATH, "rb").read())
        ts = int(_time.time())
        nonce = "test-nonce"
        msg = build_response_verify_message(ts, nonce, resp_body)
        sig = rsa_sign(msg, priv)
        return httpx.Response(
            200,
            headers={
                Headers.Timestamp: str(ts),
                Headers.Nonce: nonce,
                Headers.Signature: sig,
                Headers.Serial: PLAT_SERIAL,
            },
            content=resp_body,
        )

    httpx_mock.add_callback(handler)
    cli, raw = _make_client()
    try:
        r = cli.post("/v1/hello", json={"k": "v"})
    finally:
        raw.close()
    assert captured["auth"] is not None
    assert captured["auth"].startswith("DouyinPay-RSA ")
    assert captured["timestamp"] is None
    assert captured["nonce"] is None
    assert captured["ua"] == USER_AGENT
    assert captured["agent"] == build_sdk_agent("RSA", MCHID)
    assert r.data == {"ok": 1}
    assert r.status_code == 200


def test_local_gateway_protocol_roundtrip_verifies_request_and_response():
    merchant_key_pem, merchant_cert_pem = _make_rsa_key_and_cert("merchant")
    platform_key_pem, platform_cert_pem = _make_rsa_key_and_cert("platform")
    merchant_serial = get_certificate_serial_number(merchant_cert_pem)
    platform_serial = get_certificate_serial_number(platform_cert_pem)
    merchant_public_key = load_rsa_public_key(merchant_cert_pem)
    platform_private_key = load_rsa_private_key(platform_key_pem)
    captured = {}

    def gateway_handler(request):
        auth = _parse_authorization_header(request.headers[Headers.Authorization])
        assert auth["mchid"] == MCHID
        assert auth["serial_no"] == merchant_serial
        assert request.headers[Headers.SdkAgent] == build_sdk_agent("RSA", MCHID)

        request_target = request_target_from_url(str(request.url))
        sign_message = build_request_sign_message(
            request.method,
            request_target,
            int(auth["timestamp"]),
            auth["nonce_str"],
            request.content,
        )
        assert rsa_verify(sign_message, auth["signature"], merchant_public_key)
        captured["request_target"] = request_target
        captured["body"] = request.content.decode("utf-8")

        response_body = '{"code_url":"https://pay.example/qr","trade_state":"NOTPAY"}'
        ts = int(__import__("time").time())
        nonce = "platform-nonce"
        signature = rsa_sign(
            build_response_verify_message(ts, nonce, response_body),
            platform_private_key,
        )
        return httpx.Response(
            200,
            headers={
                Headers.Timestamp: str(ts),
                Headers.Nonce: nonce,
                Headers.Signature: signature,
                Headers.Serial: platform_serial,
            },
            content=response_body,
        )

    raw_client = httpx.Client(transport=httpx.MockTransport(gateway_handler))
    client = create_rsa_client(
        mchid=MCHID,
        serial=merchant_serial,
        private_key=merchant_key_pem,
        platform_certificate=platform_cert_pem,
        base_url="https://gateway.test",
        http_client=raw_client,
    )
    try:
        resp = client.path("/v1/trade/transactions/native").post(
            {
                "mchid": MCHID,
                "description": "协议闭环测试",
                "amount": {"currency": "CNY", "total": 1},
            },
            params={"mchid": MCHID, "debug": True},
        )
    finally:
        client.close()

    assert captured["request_target"] == "/v1/trade/transactions/native?mchid=mch-test&debug=true"
    assert captured["body"] == '{"mchid":"mch-test","description":"协议闭环测试","amount":{"currency":"CNY","total":1}}'
    assert resp.status_code == 200
    assert resp.data["code_url"] == "https://pay.example/qr"


def test_patch_method_supported(httpx_mock):
    methods = []

    def handler(request):
        methods.append(request.method)
        import time as _time
        resp_body = '{"patched":true}'
        priv = load_rsa_private_key(open(PRIV_PATH, "rb").read())
        ts = int(_time.time())
        msg = build_response_verify_message(ts, "n", resp_body)
        sig = rsa_sign(msg, priv)
        return httpx.Response(
            200,
            headers={
                Headers.Timestamp: str(ts),
                Headers.Nonce: "n",
                Headers.Signature: sig,
                Headers.Serial: PLAT_SERIAL,
            },
            content=resp_body,
        )

    httpx_mock.add_callback(handler)
    cli, raw = _make_client()
    try:
        cli.patch("/v1/x", json={"a": 1})
    finally:
        raw.close()
    assert methods == ["PATCH"]


def test_on_request_callback(httpx_mock):
    called = []

    def handler(request):
        import time as _time
        resp_body = "{}"
        priv = load_rsa_private_key(open(PRIV_PATH, "rb").read())
        ts = int(_time.time())
        msg = build_response_verify_message(ts, "n", resp_body)
        sig = rsa_sign(msg, priv)
        return httpx.Response(
            200,
            headers={
                Headers.Timestamp: str(ts),
                Headers.Nonce: "n",
                Headers.Signature: sig,
                Headers.Serial: PLAT_SERIAL,
            },
            content=resp_body,
        )

    httpx_mock.add_callback(handler)
    cfg = DouYinPayConfig(
        **BASE_CONF,
        on_request=lambda ctx: called.append(ctx),
    )
    raw_client = httpx.Client()
    cfg.http_client = raw_client
    cli = HttpClient(cfg)
    try:
        cli.get("/v1/ping", params={"q": "1"})
    finally:
        raw_client.close()
    assert len(called) == 1
    ctx = called[0]
    assert ctx["method"] == "GET"
    assert ctx["path"] == "/v1/ping"
    assert "requestTarget" in ctx and "headers" in ctx


def test_per_request_on_request_callback(httpx_mock):
    called = []
    httpx_mock.add_response(json={"ok": True})
    cli, raw = _make_client()
    try:
        cli.get("/v1/ping", skip_verify=True, on_request=lambda ctx: called.append(ctx))
    finally:
        raw.close()
    assert len(called) == 1
    assert called[0]["method"] == "GET"
    assert called[0]["path"] == "/v1/ping"


def test_user_headers_cannot_override_authorization(httpx_mock):
    captured = {}

    def handler(request):
        captured["auth"] = request.headers.get(Headers.Authorization)
        return httpx.Response(200, json={"ok": True})

    httpx_mock.add_callback(handler)
    cli, raw = _make_client()
    try:
        cli.get("/v1/ping", headers={Headers.Authorization: "bad"}, skip_verify=True)
    finally:
        raw.close()
    assert captured["auth"] != "bad"
    assert captured["auth"].startswith("DouyinPay-RSA ")


def test_base_uri_alias(httpx_mock):
    import time as _time

    def handler(request):
        assert str(request.url).startswith("https://alias.test.local/")
        resp_body = "{}"
        priv = load_rsa_private_key(open(PRIV_PATH, "rb").read())
        ts = int(_time.time())
        msg = build_response_verify_message(ts, "n", resp_body)
        sig = rsa_sign(msg, priv)
        return httpx.Response(
            200,
            headers={
                Headers.Timestamp: str(ts),
                Headers.Nonce: "n",
                Headers.Signature: sig,
                Headers.Serial: PLAT_SERIAL,
            },
            content=resp_body,
        )

    httpx_mock.add_callback(handler)
    conf = dict(BASE_CONF)
    conf["base_url"] = "https://bad.url/"
    conf["base_uri"] = "https://alias.test.local/"
    cfg = DouYinPayConfig(**conf)
    raw = httpx.Client()
    cfg.http_client = raw
    cli = HttpClient(cfg)
    try:
        cli.get("/x", skip_verify=True)
    finally:
        raw.close()


def test_skip_verify(httpx_mock):
    httpx_mock.add_response(json={"a": 1})
    cfg = DouYinPayConfig(**BASE_CONF)
    raw = httpx.Client()
    cfg.http_client = raw
    cli = HttpClient(cfg)
    try:
        r = cli.get("/x", skip_verify=True)
    finally:
        raw.close()
    assert r.data == {"a": 1}


class _OnDemandCertificateProvider:
    """初始无证书；refresh_for_serial 被调用时注入平台证书，模拟按需刷新闭环。"""

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


def test_response_verify_refreshes_on_unknown_serial(httpx_mock):
    import time as _time

    def handler(request):
        resp_body = '{"ok":true}'
        priv = load_rsa_private_key(open(PRIV_PATH, "rb").read())
        ts = int(_time.time())
        msg = build_response_verify_message(ts, "n", resp_body)
        sig = rsa_sign(msg, priv)
        return httpx.Response(
            200,
            headers={
                Headers.Timestamp: str(ts),
                Headers.Nonce: "n",
                Headers.Signature: sig,
                Headers.Serial: PLAT_SERIAL,
            },
            content=resp_body,
        )

    httpx_mock.add_callback(handler)

    provider = _OnDemandCertificateProvider({PLAT_SERIAL: CERT_PEM})
    cfg = DouYinPayConfig(
        mchid=MCHID,
        serial=MCH_SERIAL,
        private_key=open(PRIV_PATH, "rb").read(),
        certs={},
        sign_type=SignType.RSA,
        encrypt_type=EncryptType.AES,
        encrypt_key=b"a" * 32,
        certificate_provider=provider,
        base_url="https://api.test.local",
    )
    raw = httpx.Client()
    cfg.http_client = raw
    cli = HttpClient(cfg)
    try:
        r = cli.get("/v1/ping")
    finally:
        raw.close()
    assert provider.refreshed_serials == [PLAT_SERIAL]
    assert r.status_code == 200
    assert r.data == {"ok": True}


def test_response_verify_raises_when_provider_has_no_refresh(httpx_mock):
    import time as _time
    from bytedance.douyinpay.errors import DouYinPayCertificateSerialNotFound

    def handler(request):
        resp_body = '{"ok":true}'
        priv = load_rsa_private_key(open(PRIV_PATH, "rb").read())
        ts = int(_time.time())
        msg = build_response_verify_message(ts, "n", resp_body)
        sig = rsa_sign(msg, priv)
        return httpx.Response(
            200,
            headers={
                Headers.Timestamp: str(ts),
                Headers.Nonce: "n",
                Headers.Signature: sig,
                Headers.Serial: PLAT_SERIAL,
            },
            content=resp_body,
        )

    httpx_mock.add_callback(handler)

    class _ReadOnlyProvider:
        def get_certs(self):
            return {}

    cfg = DouYinPayConfig(
        mchid=MCHID,
        serial=MCH_SERIAL,
        private_key=open(PRIV_PATH, "rb").read(),
        certs={},
        sign_type=SignType.RSA,
        encrypt_type=EncryptType.AES,
        encrypt_key=b"a" * 32,
        certificate_provider=_ReadOnlyProvider(),
        base_url="https://api.test.local",
    )
    raw = httpx.Client()
    cfg.http_client = raw
    cli = HttpClient(cfg)
    try:
        with pytest.raises(DouYinPayCertificateSerialNotFound) as exc_info:
            cli.get("/v1/ping")
        assert exc_info.value.serial == PLAT_SERIAL
    finally:
        raw.close()
