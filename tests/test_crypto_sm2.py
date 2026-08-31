# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from gmssl import sm2 as gmssl_sm2, func

from bytedance.douyinpay.crypto.sm2 import (
    Sm2Signer, load_sm2_private_key, load_sm2_public_key,
    sm2_sign, sm2_verify,
)


def _sm2_keypair():
    table = gmssl_sm2.default_ecc_table
    n = int(table["n"], 16)
    g = table["g"]
    import secrets
    while True:
        d_hex = secrets.token_hex(32)
        d = int(d_hex, 16)
        if 1 <= d < n:
            break
    tmp = gmssl_sm2.CryptSM2(private_key=d_hex, public_key="0" * 128)
    pub_hex = tmp._kg(d, g)
    return gmssl_sm2.CryptSM2(private_key=d_hex, public_key=pub_hex)


def test_sm2_signer_with_ec_key():
    pair = _sm2_keypair()
    signer = Sm2Signer(private_key=pair, public_key=pair)
    msg = "SM2withSM3 test message"
    sig = signer.sign(msg)
    assert isinstance(sig, str) and len(sig) > 0
    assert signer.verify(msg, sig) is True


def test_sm2_verify_tampered_fails():
    pair = _sm2_keypair()
    signer = Sm2Signer(private_key=pair, public_key=pair)
    sig = signer.sign("original")
    assert signer.verify("tampered", sig) is False
    assert signer.sign_type == "SM2"


def test_sm2_functional_api():
    pair = _sm2_keypair()
    msg = "functional api test"
    sig = sm2_sign(msg, pair)
    assert sm2_verify(msg, sig, pair) is True
    assert sm2_verify(msg + "x", sig, pair) is False


def test_sm2_separate_verifier():
    signer_pair = _sm2_keypair()
    msg = "hello"
    sig = sm2_sign(msg, signer_pair)
    verifier = gmssl_sm2.CryptSM2(private_key="0" * 64, public_key=signer_pair.public_key)
    assert sm2_verify(msg, sig, verifier) is True


def test_load_sm2_key_roundtrip_via_pem(tmp_path):
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import serialization
    priv_ec = ec.generate_private_key(ec.SECP256R1())
    pem_bytes = priv_ec.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    p = tmp_path / "ec_priv.pem"
    p.write_bytes(pem_bytes)
    loaded = load_sm2_private_key(str(p))
    assert loaded is not None
    assert loaded.private_key is not None
    assert loaded.public_key is not None
