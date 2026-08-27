import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import re
import time
from douyinpay.formatter import (
    generate_nonce, generate_timestamp, build_authorization,
    build_request_sign_message, build_response_verify_message,
)
from douyinpay.constants import DEFAULT_NONCE_SIZE, AUTHORIZATION_TYPE


def test_generate_nonce_length():
    n = generate_nonce()
    assert len(n) == DEFAULT_NONCE_SIZE


def test_generate_nonce_charset():
    n = generate_nonce()
    assert re.fullmatch(r'[A-Za-z0-9]+', n) is not None


def test_generate_nonce_uniqueness():
    a = generate_nonce()
    b = generate_nonce()
    assert a != b


def test_generate_timestamp_is_seconds():
    t = generate_timestamp()
    assert isinstance(t, int)
    assert t > 0
    now = int(time.time())
    assert abs(t - now) < 5


def test_build_authorization_format():
    auth = build_authorization("mchid1", "nonce1", "sig1", 1234567890, "serial1")
    assert auth.startswith(f"{AUTHORIZATION_TYPE} ")
    assert 'mchid="mchid1"' in auth
    assert 'serial_no="serial1"' in auth
    assert 'timestamp="1234567890"' in auth
    assert 'nonce_str="nonce1"' in auth
    assert 'signature="sig1"' in auth


def test_build_request_sign_message_newline_end():
    msg = build_request_sign_message("POST", "/v1/x?a=1", 1000, "abc", '{"k":"v"}')
    assert msg == "POST\n/v1/x?a=1\n1000\nabc\n{\"k\":\"v\"}\n"


def test_build_request_sign_message_method_upper():
    msg = build_request_sign_message("post", "/p", 1, "n", "")
    assert msg.startswith("POST\n")


def test_build_request_sign_message_empty_body():
    msg = build_request_sign_message("GET", "/p", 1, "n")
    assert "1\nn\n\n" in msg[-5:]


def test_build_response_verify_message():
    msg = build_response_verify_message(1000, "abc", "body")
    assert msg == "1000\nabc\nbody\n"


def test_build_response_verify_message_empty_body():
    msg = build_response_verify_message(1, "n")
    assert msg == "1\nn\n\n"
