import json
from dataclasses import dataclass
from typing import Dict, Any, Optional, Generic, TypeVar, Union

from .config import CertificateProvider, KeyLike
from .constants import SignType, DEFAULT_MAX_CLOCK_OFFSET, ERR_CALLBACK_ALGORITHM
from .errors import DouYinPayError
from .signer import verify_response
from .crypto.aes import aes_decrypt
from .crypto.sm4 import sm4_decrypt

T = TypeVar("T")


@dataclass
class EncryptedResource:
    algorithm: str
    ciphertext: str
    nonce: str
    associated_data: str = ""
    plaintext: Optional[str] = None


@dataclass
class NotifyRequest(Generic[T]):
    id: Optional[str] = None
    create_time: Optional[str] = None
    event_type: Optional[str] = None
    resource_type: Optional[str] = None
    resource: Optional[EncryptedResource] = None
    summary: Optional[str] = None
    content: Optional[T] = None


class CallbackHandler:
    def __init__(
        self,
        encrypt_key: str,
        certs: Optional[Dict[str, KeyLike]] = None,
        certificate_provider: Optional[CertificateProvider] = None,
        sign_type: str = SignType.RSA,
        max_clock_offset: int = DEFAULT_MAX_CLOCK_OFFSET,
    ):
        self.encrypt_key = encrypt_key
        self.certs = certs or {}
        self.certificate_provider = certificate_provider
        self.sign_type = sign_type
        self.max_clock_offset = max_clock_offset

    def parse(self, headers: Dict[str, Any], body: Union[str, bytes]) -> NotifyRequest:
        raw_body = body.decode("utf-8") if isinstance(body, bytes) else body
        current_certs = dict(self.certs)
        if self.certificate_provider:
            try:
                current_certs.update(self.certificate_provider.get_certs())
            except Exception:
                pass
        verify_response(
            headers,
            raw_body,
            current_certs,
            self.sign_type,
            None,
            self.max_clock_offset,
        )
        notify_dict = json.loads(raw_body)
        resource_dict = notify_dict.get("resource")
        if not resource_dict:
            raise DouYinPayError("callback resource field is required")
        algorithm = resource_dict.get("algorithm", "")
        algo_upper = algorithm.upper()
        if "AES" in algo_upper or "GCM" in algo_upper:
            plaintext = aes_decrypt(
                resource_dict["ciphertext"],
                self.encrypt_key,
                resource_dict.get("nonce", ""),
                resource_dict.get("associated_data", ""),
            )
        elif "SM4" in algo_upper or "CBC" in algo_upper:
            plaintext = sm4_decrypt(
                resource_dict["ciphertext"],
                self.encrypt_key,
                resource_dict.get("nonce", ""),
                resource_dict.get("associated_data", ""),
            )
        else:
            raise DouYinPayError(ERR_CALLBACK_ALGORITHM % algorithm)
        resource = EncryptedResource(
            algorithm=algorithm,
            ciphertext=resource_dict["ciphertext"],
            nonce=resource_dict.get("nonce", ""),
            associated_data=resource_dict.get("associated_data", ""),
            plaintext=plaintext,
        )
        content = json.loads(plaintext)
        return NotifyRequest(
            id=notify_dict.get("id"),
            create_time=notify_dict.get("create_time"),
            event_type=notify_dict.get("event_type"),
            resource_type=notify_dict.get("resource_type"),
            resource=resource,
            summary=notify_dict.get("summary"),
            content=content,
        )


def parse_callback(
    headers: Dict[str, Any],
    body: Union[str, bytes],
    encrypt_key: str,
    certs: Optional[Dict[str, KeyLike]] = None,
    certificate_provider: Optional[CertificateProvider] = None,
    sign_type: str = SignType.RSA,
    **kwargs,
) -> NotifyRequest:
    handler = CallbackHandler(
        encrypt_key=encrypt_key,
        certs=certs,
        certificate_provider=certificate_provider,
        sign_type=sign_type,
        **kwargs,
    )
    return handler.parse(headers, body)
