import os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')

from douyinpay.utils.pem import (
    read_key_data, is_pem_certificate,
    get_certificate_serial_number, add_certificate,
)


def test_read_key_data_bytes():
    assert read_key_data(b"abc") == b"abc"


def test_read_key_data_str_to_bytes():
    assert read_key_data("abc") == b"abc"


def test_read_key_data_file_path():
    p = os.path.join(FIXTURES, "rsa_platform_cert.pem")
    data = read_key_data(p)
    assert b"BEGIN CERTIFICATE" in data


def test_is_pem_certificate_positive():
    p = os.path.join(FIXTURES, "rsa_platform_cert.pem")
    assert is_pem_certificate(p) is True


def test_is_pem_certificate_negative_private_key():
    p = os.path.join(FIXTURES, "rsa_merchant_key.pem")
    assert is_pem_certificate(p) is False


def test_get_certificate_serial_number_format():
    p = os.path.join(FIXTURES, "rsa_platform_cert.pem")
    s = get_certificate_serial_number(p)
    assert len(s) > 0
    assert s.upper() == s
    assert ":" not in s


def test_add_certificate_dual_serial():
    cert_p = os.path.join(FIXTURES, "rsa_platform_cert.pem")
    parsed_serial = get_certificate_serial_number(cert_p)
    certs = {}
    add_certificate(certs, cert_p, "MY-CUSTOM-SERIAL")
    assert "MY-CUSTOM-SERIAL" in certs
    assert parsed_serial in certs
    assert certs["MY-CUSTOM-SERIAL"] == certs[parsed_serial]
