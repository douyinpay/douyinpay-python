import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')

from douyinpay.crypto.rsa import (
    load_rsa_private_key, load_rsa_public_key,
    rsa_sign, rsa_verify, RsaSigner,
)


def test_rsa_load_keys():
    priv = load_rsa_private_key(os.path.join(FIXTURES, "rsa_merchant_key.pem"))
    assert priv is not None
    pub = load_rsa_public_key(os.path.join(FIXTURES, "rsa_platform_cert.pem"))
    assert pub is not None


def test_rsa_sign_and_verify_success():
    priv = load_rsa_private_key(os.path.join(FIXTURES, "rsa_merchant_key.pem"))
    msg = "POST\n/v1/x\n1\na\n{}\n"
    sig = rsa_sign(msg, priv)
    assert isinstance(sig, str) and len(sig) > 0
    from cryptography.hazmat.primitives import serialization
    pub_raw = priv.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    pub = load_rsa_public_key(pub_raw)
    assert rsa_verify(msg, sig, pub) is True


def test_rsa_verify_tampered_message_fails():
    priv = load_rsa_private_key(os.path.join(FIXTURES, "rsa_merchant_key.pem"))
    msg = "test message"
    sig = rsa_sign(msg, priv)
    from cryptography.hazmat.primitives import serialization
    pub_raw = priv.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    pub = load_rsa_public_key(pub_raw)
    assert rsa_verify("tampered message", sig, pub) is False


def test_rsa_signer_class():
    priv = load_rsa_private_key(os.path.join(FIXTURES, "rsa_merchant_key.pem"))
    from cryptography.hazmat.primitives import serialization
    pub_raw = priv.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    signer = RsaSigner(private_key=priv)
    sig = signer.sign("hello")
    pub = load_rsa_public_key(pub_raw)
    assert signer.verify("hello", sig, public_key=pub) is True
    assert signer.verify("other", sig, public_key=pub) is False
    assert signer.sign_type == "RSA"
