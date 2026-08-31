# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

import os, sys, base64
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from bytedance.douyinpay.crypto.aes import aes_encrypt, aes_decrypt, AesGcmEncryptor, _key_bytes
from bytedance.douyinpay.errors import DouYinPayError
from bytedance.douyinpay.constants import ERR_AES_KEY_LENGTH


TEST_KEY_32 = b"a" * 32
TEST_KEY_B64 = base64.b64encode(TEST_KEY_32).decode()
TEST_NONCE = b"0123456789ab"  # 12 bytes


def test_key_bytes_direct_32():
    assert len(_key_bytes(TEST_KEY_32)) == 32


def test_key_bytes_base64_44():
    assert _key_bytes(TEST_KEY_B64) == TEST_KEY_32


def test_key_bytes_invalid_length():
    with pytest.raises(DouYinPayError, match=ERR_AES_KEY_LENGTH.split()[0]):
        _key_bytes(b"short")


def test_aes_roundtrip():
    plain = "{\"amount\":100}"
    ct = aes_encrypt(plain, TEST_KEY_32, TEST_NONCE, aad="order")
    dec = aes_decrypt(ct, TEST_KEY_32, TEST_NONCE, aad="order")
    assert dec == plain


def test_aes_tamper_ciphertext_fails():
    ct = aes_encrypt("hello", TEST_KEY_32, TEST_NONCE)
    bad_ct = base64.b64encode(b"A" * len(base64.b64decode(ct))).decode()
    with pytest.raises(Exception):
        aes_decrypt(bad_ct, TEST_KEY_32, TEST_NONCE)


def test_aes_tamper_aad_fails():
    ct = aes_encrypt("hello", TEST_KEY_32, TEST_NONCE, aad="good")
    with pytest.raises(Exception):
        aes_decrypt(ct, TEST_KEY_32, TEST_NONCE, aad="bad")


def test_aes_encryptor_class():
    enc = AesGcmEncryptor()
    assert enc.encrypt_type == "AES"
    pt = "plain text"
    ct = enc.encrypt(pt, TEST_KEY_32, TEST_NONCE)
    assert enc.decrypt(ct, TEST_KEY_32, TEST_NONCE) == pt
