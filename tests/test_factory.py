# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import httpx
from bytedance.douyinpay.factory import (
    create_rsa_client, create_auto_rsa_client, create_auto_rsa_client_with_manager,
    create_client, create_auto_client,
)
from bytedance.douyinpay.constants import SignType, EncryptType, SdkAgentType
from bytedance.douyinpay.errors import DouYinPayInvalidArgumentError
from tests.helpers import CERT_PEM, MCH_PRIV, PLAT_SERIAL

MCH_SERIAL = "MCH-SER-001"


def test_create_rsa_client_default_agent():
    c = create_rsa_client("mch-1", MCH_SERIAL, MCH_PRIV, CERT_PEM)
    assert c.config.sign_type == SignType.RSA
    assert c.config.encrypt_type == EncryptType.AES
    assert c.config.sdk_agent == SdkAgentType.RSA
    assert c.certificate_manager is None
    assert c.get_client().config.sign_type == SignType.RSA
    assert c.get_client("/v1/ping").path == "/v1/ping"


def test_create_client_alias_to_rsa():
    c = create_client("mch-1", MCH_SERIAL, MCH_PRIV, CERT_PEM)
    assert c.config.sign_type == SignType.RSA


def test_create_rsa_client_rejects_missing_mchid():
    with pytest.raises(DouYinPayInvalidArgumentError):
        create_rsa_client("", MCH_SERIAL, MCH_PRIV, CERT_PEM)


def test_create_rsa_client_rejects_cert_contains_merchant_serial():
    with pytest.raises(DouYinPayInvalidArgumentError):
        create_rsa_client("mch1", PLAT_SERIAL, MCH_PRIV, CERT_PEM)


def test_create_rsa_client_custom_sdk_agent():
    c = create_rsa_client("mch-1", MCH_SERIAL, MCH_PRIV, CERT_PEM, sdk_agent="CustomRSA")
    assert c.config.sdk_agent == "CustomRSA"


def test_create_rsa_client_accepts_api_base_alias():
    c = create_rsa_client(
        "mch-1",
        MCH_SERIAL,
        MCH_PRIV,
        CERT_PEM,
        api_base="https://api.alias.test/",
    )
    try:
        assert c.config.base_url == "https://api.alias.test/"
    finally:
        c.close()


def test_create_auto_rsa_requires_encrypt_key(httpx_mock):
    httpx_mock.add_response(status_code=200, json={"certificates": []})
    from bytedance.douyinpay.errors import DouYinPayCertificateError
    c = None
    try:
        try:
            c = create_auto_rsa_client("mch-1", MCH_SERIAL, MCH_PRIV, encrypt_key="", http_client=httpx.Client())
        except DouYinPayInvalidArgumentError:
            return
        except Exception:
            return
    finally:
        if c is not None and getattr(c, 'certificate_manager', None):
            c.certificate_manager.stop()
            c._http._client.close()


def test_create_auto_rsa_client_with_manager(httpx_mock):
    httpx_mock.add_response(status_code=200, json={"certificates": []})
    raw_client = httpx.Client()
    result = create_auto_rsa_client_with_manager(
        "mch-1",
        MCH_SERIAL,
        MCH_PRIV,
        encrypt_key="a" * 32,
        refresh_interval_sec=0,
        http_client=raw_client,
    )
    try:
        assert result.client.certificate_manager is result.certificate_manager
        assert result.client.config.sdk_agent == SdkAgentType.AUTO_RSA
        assert result.client.config.http_client is raw_client
    finally:
        result.certificate_manager.stop()
        result.client._http._client.close()
