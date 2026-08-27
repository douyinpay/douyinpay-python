import base64
from typing import Union

from .base import EncryptorBase
from ..errors import DouYinPayError
from ..constants import ERR_SM4_KEY_LENGTH


def _to_bytes(data: Union[str, bytes, None]) -> bytes:
    if data is None:
        return b""
    if isinstance(data, bytes):
        return data
    return data.encode("utf-8")


def _key_bytes(key: Union[str, bytes]) -> bytes:
    kb = _to_bytes(key)
    if len(kb) == 24:
        try:
            import base64 as _b64
            decoded = _b64.b64decode(kb)
            if len(decoded) == 16:
                return decoded
        except Exception:
            pass
    if len(kb) != 16:
        raise DouYinPayError(ERR_SM4_KEY_LENGTH)
    return kb


def _pkcs5_pad(data: bytes, block_size: int = 16) -> bytes:
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len] * pad_len)


def _pkcs5_unpad(data: bytes) -> bytes:
    if not data:
        return data
    pad_len = data[-1]
    if pad_len < 1 or pad_len > 16:
        return data
    if data[-pad_len:] != bytes([pad_len] * pad_len):
        return data
    return data[:-pad_len]


def sm4_encrypt(
    plaintext: Union[str, bytes],
    key: Union[str, bytes],
    nonce: Union[str, bytes],
    aad: Union[str, bytes] = b"",
) -> str:
    from gmssl.sm4 import CryptSM4, SM4_ENCRYPT
    kb = _key_bytes(key)
    nb = _to_bytes(nonce)
    if len(nb) < 16:
        nb = (nb + b"\x00" * 16)[:16]
    elif len(nb) > 16:
        nb = nb[:16]
    pt = _to_bytes(plaintext)
    sm4 = CryptSM4()
    sm4.set_key(kb, SM4_ENCRYPT)
    ct = sm4.crypt_cbc(nb, pt)
    return base64.b64encode(ct).decode("utf-8")


def sm4_decrypt(
    ciphertext: str,
    key: Union[str, bytes],
    nonce: Union[str, bytes],
    aad: Union[str, bytes] = b"",
) -> str:
    from gmssl.sm4 import CryptSM4, SM4_DECRYPT
    kb = _key_bytes(key)
    nb = _to_bytes(nonce)
    if len(nb) < 16:
        nb = (nb + b"\x00" * 16)[:16]
    elif len(nb) > 16:
        nb = nb[:16]
    ct = base64.b64decode(ciphertext)
    sm4 = CryptSM4()
    sm4.set_key(kb, SM4_DECRYPT)
    pt = sm4.crypt_cbc(nb, ct)
    return pt.decode("utf-8")


class Sm4CbcEncryptor(EncryptorBase):
    encrypt_type = "SM4"

    def encrypt(self, plaintext, key, nonce, aad=b"") -> str:
        return sm4_encrypt(plaintext, key, nonce, aad)

    def decrypt(self, ciphertext, key, nonce, aad=b"") -> str:
        return sm4_decrypt(ciphertext, key, nonce, aad)
