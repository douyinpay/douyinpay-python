# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

import base64
from typing import Union, Tuple

from .base import SignerBase, KeyLike
from ..utils.pem import read_key_data
from ..errors import DouYinPaySignatureError


def _to_bytes(data: Union[str, bytes]) -> bytes:
    if isinstance(data, bytes):
        return data
    return data.encode("utf-8")


def _ec_priv_to_hex_keys(priv) -> Tuple[str, str]:
    from cryptography.hazmat.primitives.asymmetric import ec
    numbers = priv.private_numbers()
    d_hex = "%064x" % numbers.private_value
    pub_nums = priv.public_key().public_numbers()
    pub_hex = "%064x%064x" % (pub_nums.x, pub_nums.y)
    return d_hex, pub_hex


def _ec_pub_to_hex(pub) -> str:
    from cryptography.hazmat.primitives.asymmetric import ec
    nums = pub.public_numbers()
    return "%064x%064x" % (nums.x, nums.y)


_DUMMY_PUB_HEX = "0" * 128


def load_sm2_private_key(key_data: KeyLike):
    from gmssl import sm2
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    raw = read_key_data(key_data)
    try:
        text = raw.decode("utf-8")
    except Exception:
        text = ""
    if "-----BEGIN" in text and "PRIVATE KEY-----" in text:
        try:
            priv_bytes = text.encode()
            priv = serialization.load_pem_private_key(priv_bytes, password=None)
            if isinstance(priv, ec.EllipticCurvePrivateKey):
                d_hex, pub_hex = _ec_priv_to_hex_keys(priv)
                return sm2.CryptSM2(private_key=d_hex, public_key=pub_hex)
        except Exception:
            pass
    raw_bytes = raw if isinstance(raw, bytes) else raw.encode("utf-8")
    if len(raw_bytes) >= 64:
        try:
            priv_hex = raw_bytes[:64].decode("ascii")
            int(priv_hex, 16)
            return sm2.CryptSM2(private_key=priv_hex, public_key=_DUMMY_PUB_HEX)
        except Exception:
            pass
    if len(raw_bytes) == 32:
        priv_hex = raw_bytes.hex()
        return sm2.CryptSM2(private_key=priv_hex, public_key=_DUMMY_PUB_HEX)
    priv_hex = raw_bytes[:32].hex()
    return sm2.CryptSM2(private_key=priv_hex, public_key=_DUMMY_PUB_HEX)


def load_sm2_public_key(key_data: KeyLike):
    from gmssl import sm2
    from cryptography import x509
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    raw = read_key_data(key_data)
    try:
        text = raw.decode("utf-8")
    except Exception:
        text = ""
    if "-----BEGIN" in text and ("CERTIFICATE-----" in text or "PUBLIC KEY-----" in text):
        try:
            input_bytes = text.encode()
            pub = None
            try:
                cert = x509.load_pem_x509_certificate(input_bytes)
                pub = cert.public_key()
            except Exception:
                try:
                    pub = serialization.load_pem_public_key(input_bytes)
                except Exception:
                    pub = None
            if pub is not None and isinstance(pub, ec.EllipticCurvePublicKey):
                pub_hex = _ec_pub_to_hex(pub)
                return sm2.CryptSM2(private_key="0" * 64, public_key=pub_hex)
        except Exception:
            pass
    raw_bytes = raw if isinstance(raw, bytes) else raw.encode()
    if len(raw_bytes) >= 128:
        try:
            pub_hex = raw_bytes[:128].decode("ascii")
            int(pub_hex, 16)
            return sm2.CryptSM2(private_key="0" * 64, public_key=pub_hex)
        except Exception:
            pass
    if len(raw_bytes) == 65 and raw_bytes[0] == 0x04:
        pub_hex = raw_bytes[1:].hex()
        return sm2.CryptSM2(private_key="0" * 64, public_key=pub_hex)
    if len(raw_bytes) == 64:
        pub_hex = raw_bytes.hex()
        return sm2.CryptSM2(private_key="0" * 64, public_key=pub_hex)
    pub_hex = raw_bytes[:64].hex() if len(raw_bytes) >= 64 else raw_bytes.hex().ljust(128, "0")
    return sm2.CryptSM2(private_key="0" * 64, public_key=pub_hex)


def sm2_sign(message: Union[str, bytes], private_key) -> str:
    from gmssl import func
    msg_bytes = _to_bytes(message)
    rand_hex = func.random_hex(64)
    sig = private_key.sign(msg_bytes, rand_hex)
    if sig is None:
        raise DouYinPaySignatureError("SM2 signing returned None; retry")
    sig_bytes = bytes.fromhex(sig)
    return base64.b64encode(sig_bytes).decode("utf-8")


def sm2_encrypt(plaintext: Union[str, bytes], public_key) -> str:
    pt_bytes = _to_bytes(plaintext)
    ct = public_key.encrypt(pt_bytes)
    if ct is None:
        raise DouYinPaySignatureError("SM2 encryption returned None")
    if isinstance(ct, bytes):
        ct_bytes = ct
    else:
        ct_bytes = bytes.fromhex(str(ct))
    return base64.b64encode(ct_bytes).decode("utf-8")


def sm2_verify(message: Union[str, bytes], signature: str, public_key) -> bool:
    msg_bytes = _to_bytes(message)
    try:
        sig_bytes = base64.b64decode(signature)
    except Exception:
        return False
    sig_hex = sig_bytes.hex()
    try:
        result = public_key.verify(sig_hex, msg_bytes)
        return bool(result)
    except Exception:
        return False


class Sm2Signer(SignerBase):
    sign_type = "SM2"

    def __init__(self, private_key=None, public_key=None):
        self._private_key = private_key
        self._public_key = public_key

    def sign(self, message: str) -> str:
        if self._private_key is None:
            raise DouYinPaySignatureError("SM2 private key not provided for signing")
        return sm2_sign(message, self._private_key)

    def verify(self, message: str, signature: str, public_key=None) -> bool:
        pub = public_key or self._public_key
        if pub is None:
            raise DouYinPaySignatureError("SM2 public key not provided for verifying")
        return sm2_verify(message, signature, pub)
