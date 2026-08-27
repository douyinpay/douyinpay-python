import base64
from typing import Union

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature

from .base import SignerBase, KeyLike
from ..utils.pem import read_key_data
from ..errors import DouYinPaySignatureError


def _to_bytes(data: Union[str, bytes]) -> bytes:
    if isinstance(data, bytes):
        return data
    return data.encode("utf-8")


def load_rsa_private_key(key_data: KeyLike):
    raw = read_key_data(key_data)
    private_key = serialization.load_pem_private_key(raw, password=None)
    if not isinstance(private_key, rsa.RSAPrivateKey):
        raise DouYinPaySignatureError("loaded key is not an RSA private key")
    return private_key


def load_rsa_public_key(key_data: KeyLike):
    raw = read_key_data(key_data)
    candidates = []
    try:
        key = serialization.load_pem_public_key(raw)
        candidates.append(key)
    except Exception:
        pass
    try:
        from cryptography import x509
        cert = x509.load_pem_x509_certificate(raw)
        candidates.append(cert.public_key())
    except Exception:
        pass
    for key in candidates:
        if isinstance(key, rsa.RSAPublicKey):
            return key
    raise DouYinPaySignatureError("failed to load RSA public key from provided data")


def rsa_sign(message: Union[str, bytes], private_key) -> str:
    msg_bytes = _to_bytes(message)
    signature = private_key.sign(
        msg_bytes,
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode("utf-8")


def rsa_encrypt(plaintext: Union[str, bytes], public_key) -> str:
    pt_bytes = _to_bytes(plaintext)
    ciphertext = public_key.encrypt(
        pt_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return base64.b64encode(ciphertext).decode("utf-8")


def rsa_verify(message: Union[str, bytes], signature: str, public_key) -> bool:
    msg_bytes = _to_bytes(message)
    try:
        sig_bytes = base64.b64decode(signature)
    except Exception as e:
        raise DouYinPaySignatureError(f"invalid base64 signature: {e}")
    try:
        public_key.verify(
            sig_bytes,
            msg_bytes,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return True
    except InvalidSignature:
        return False
    except Exception:
        return False


class RsaSigner(SignerBase):
    sign_type = "RSA"

    def __init__(self, private_key=None, public_key=None):
        self._private_key = private_key
        self._public_key = public_key

    def sign(self, message: str) -> str:
        if self._private_key is None:
            raise DouYinPaySignatureError("RSA private key not provided for signing")
        return rsa_sign(message, self._private_key)

    def verify(self, message: str, signature: str, public_key=None) -> bool:
        pub = public_key or self._public_key
        if pub is None:
            raise DouYinPaySignatureError("RSA public key not provided for verifying")
        return rsa_verify(message, signature, pub)
