import os, sys, base64
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from douyinpay.crypto.sm4 import (
    sm4_encrypt, sm4_decrypt, Sm4CbcEncryptor,
    _pkcs5_pad, _pkcs5_unpad,
)
from douyinpay.errors import DouYinPayError


TEST_KEY_16 = b"0123456789ABCDEF"
TEST_IV_16 = b"ABCDEF0123456789"


def test_pkcs5_pad_unpad_roundtrip():
    for size in [0, 1, 15, 16, 17, 31, 32]:
        data = b"A" * size
        padded = _pkcs5_pad(data)
        assert len(padded) % 16 == 0
        assert _pkcs5_unpad(padded) == data


def test_sm4_roundtrip():
    plain = "国密SM4测试123"
    ct = sm4_encrypt(plain, TEST_KEY_16, TEST_IV_16)
    assert isinstance(ct, str)
    dec = sm4_decrypt(ct, TEST_KEY_16, TEST_IV_16)
    assert dec == plain


def test_sm4_invalid_key_length():
    with pytest.raises(DouYinPayError):
        sm4_encrypt("x", b"short", TEST_IV_16)


def test_sm4_iv_padded_to_16():
    short_iv = b"short"
    ct = sm4_encrypt("hello", TEST_KEY_16, short_iv)
    dec = sm4_decrypt(ct, TEST_KEY_16, short_iv)
    assert dec == "hello"


def test_sm4_encryptor_class():
    enc = Sm4CbcEncryptor()
    assert enc.encrypt_type == "SM4"
    pt = "payment data 测试"
    ct = enc.encrypt(pt, TEST_KEY_16, TEST_IV_16)
    assert enc.decrypt(ct, TEST_KEY_16, TEST_IV_16) == pt
