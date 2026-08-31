# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

import base64
from typing import Union

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .base import EncryptorBase
from ..errors import DouYinPayError
from ..constants import ERR_AES_KEY_LENGTH


def _to_bytes(data: Union[str, bytes, None]) -> bytes:
    if data is None:
        return b""
    if isinstance(data, bytes):
        return data
    return data.encode("utf-8")


def _key_bytes(key: Union[str, bytes]) -> bytes:
    kb = _to_bytes(key)
    if len(kb) == 44:
        try:
            import base64 as _b64
            decoded = _b64.b64decode(kb)
            if len(decoded) == 32:
                return decoded
        except Exception:
            pass
    if len(kb) != 32:
        raise DouYinPayError(ERR_AES_KEY_LENGTH)
    return kb


def aes_encrypt(
    plaintext: Union[str, bytes],
    key: Union[str, bytes],
    nonce: Union[str, bytes],
    aad: Union[str, bytes] = b"",
) -> str:
    kb = _key_bytes(key)
    nb = _to_bytes(nonce)
    ab = _to_bytes(aad)
    pt = _to_bytes(plaintext)
    aesgcm = AESGCM(kb)
    ct = aesgcm.encrypt(nb, pt, ab)
    return base64.b64encode(ct).decode("utf-8")


def aes_decrypt(
    ciphertext: str,
    key: Union[str, bytes],
    nonce: Union[str, bytes],
    aad: Union[str, bytes] = b"",
) -> str:
    kb = _key_bytes(key)
    nb = _to_bytes(nonce)
    ab = _to_bytes(aad)
    ct = base64.b64decode(ciphertext)
    aesgcm = AESGCM(kb)
    pt = aesgcm.decrypt(nb, ct, ab)
    return pt.decode("utf-8")


class AesGcmEncryptor(EncryptorBase):
    encrypt_type = "AES"

    def encrypt(self, plaintext, key, nonce, aad=b"") -> str:
        return aes_encrypt(plaintext, key, nonce, aad)

    def decrypt(self, ciphertext, key, nonce, aad=b"") -> str:
        return aes_decrypt(ciphertext, key, nonce, aad)
