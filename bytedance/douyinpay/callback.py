# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

import json
from dataclasses import dataclass
from typing import Any, Dict, Generic, Optional, TypeVar, Union

from .config import CertificateProvider, KeyLike
from .constants import DEFAULT_MAX_CLOCK_OFFSET, ERR_CALLBACK_ALGORITHM, SignType
from .crypto.aes import aes_decrypt
from .errors import DouYinPayError, DouYinPayCertificateSerialNotFound
from .signer import verify_response

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
        encrypt_key: KeyLike,
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

    @classmethod
    def from_client(
        cls,
        client: Any,
        encrypt_key: Optional[KeyLike] = None,
        certs: Optional[Dict[str, KeyLike]] = None,
        certificate_provider: Optional[CertificateProvider] = None,
        sign_type: Optional[str] = None,
        max_clock_offset: Optional[int] = None,
    ) -> "CallbackHandler":
        config = getattr(client, "config", None)
        if config is None:
            raise DouYinPayError("client must be a DouyinPayClient")

        resolved_encrypt_key = encrypt_key if encrypt_key is not None else getattr(config, "encrypt_key", None)
        if not resolved_encrypt_key:
            raise DouYinPayError("encrypt_key is required for callback")

        current_certs = dict(getattr(config, "certs", None) or {})
        if certs:
            current_certs.update(certs)

        return cls(
            encrypt_key=resolved_encrypt_key,
            certs=current_certs,
            certificate_provider=certificate_provider
            if certificate_provider is not None
            else getattr(config, "certificate_provider", None),
            sign_type=sign_type or getattr(config, "sign_type", SignType.RSA),
            max_clock_offset=max_clock_offset
            if max_clock_offset is not None
            else getattr(config, "max_clock_offset", DEFAULT_MAX_CLOCK_OFFSET),
        )

    def _current_certs(self) -> Dict[str, KeyLike]:
        current_certs = dict(self.certs)
        if self.certificate_provider:
            try:
                current_certs.update(self.certificate_provider.get_certs())
            except Exception:
                pass
        return current_certs

    def _verify(self, headers: Dict[str, Any], raw_body: str) -> None:
        try:
            verify_response(
                headers,
                raw_body,
                self._current_certs(),
                self.sign_type,
                None,
                self.max_clock_offset,
            )
        except DouYinPayCertificateSerialNotFound as exc:
            refresh_for_serial = getattr(self.certificate_provider, "refresh_for_serial", None)
            if refresh_for_serial is None:
                raise
            refresh_for_serial(exc.serial)
            verify_response(
                headers,
                raw_body,
                self._current_certs(),
                self.sign_type,
                None,
                self.max_clock_offset,
            )

    def parse(self, headers: Dict[str, Any], body: Union[str, bytes]) -> NotifyRequest:
        raw_body = body.decode("utf-8") if isinstance(body, bytes) else body
        self._verify(headers, raw_body)
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
    encrypt_key: Optional[KeyLike] = None,
    certs: Optional[Dict[str, KeyLike]] = None,
    certificate_provider: Optional[CertificateProvider] = None,
    sign_type: Optional[str] = None,
    client: Optional[Any] = None,
    **kwargs,
) -> NotifyRequest:
    if client is not None:
        handler = CallbackHandler.from_client(
            client,
            encrypt_key=encrypt_key,
            certs=certs,
            certificate_provider=certificate_provider,
            sign_type=sign_type,
            max_clock_offset=kwargs.pop("max_clock_offset", None),
        )
        if kwargs:
            unexpected = ", ".join(kwargs.keys())
            raise TypeError(f"unexpected callback option(s): {unexpected}")
        return handler.parse(headers, body)

    if not encrypt_key:
        raise DouYinPayError("encrypt_key is required for callback")

    handler = CallbackHandler(
        encrypt_key=encrypt_key,
        certs=certs,
        certificate_provider=certificate_provider,
        sign_type=sign_type or SignType.RSA,
        **kwargs,
    )
    return handler.parse(headers, body)
