# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from bytedance.douyinpay.utils.pem import (
    read_key_data, is_pem_certificate,
    get_certificate_serial_number, add_certificate,
)
from tests.helpers import CERT_PEM, MCH_PRIV, PLAT_SERIAL, write_pem


def test_read_key_data_bytes():
    assert read_key_data(b"abc") == b"abc"


def test_read_key_data_str_to_bytes():
    assert read_key_data("abc") == b"abc"


def test_read_key_data_file_path(tmp_path):
    p = write_pem(tmp_path, "rsa_platform_cert.pem", CERT_PEM)
    data = read_key_data(p)
    assert b"BEGIN CERTIFICATE" in data


def test_is_pem_certificate_positive(tmp_path):
    p = write_pem(tmp_path, "rsa_platform_cert.pem", CERT_PEM)
    assert is_pem_certificate(p) is True


def test_is_pem_certificate_negative_private_key(tmp_path):
    p = write_pem(tmp_path, "rsa_merchant_key.pem", MCH_PRIV)
    assert is_pem_certificate(p) is False


def test_get_certificate_serial_number_format():
    s = get_certificate_serial_number(CERT_PEM)
    assert len(s) > 0
    assert s.upper() == s
    assert ":" not in s


def test_add_certificate_dual_serial():
    certs = {}
    add_certificate(certs, CERT_PEM, "MY-CUSTOM-SERIAL")
    assert "MY-CUSTOM-SERIAL" in certs
    assert PLAT_SERIAL in certs
    assert certs["MY-CUSTOM-SERIAL"] == certs[PLAT_SERIAL]
