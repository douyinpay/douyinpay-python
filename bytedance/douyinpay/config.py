# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from typing import Dict, Optional, Union, Any, Callable
from abc import ABC, abstractmethod

from .constants import (
    SignType,
    EncryptType,
    DEFAULT_BASE_URL,
    DEFAULT_MAX_CLOCK_OFFSET,
    DEFAULT_TIMEOUT,
    ERR_INIT_MCHID_MANDATORY,
    ERR_INIT_SERIAL_MANDATORY,
    ERR_INIT_PRIVATE_KEY_MANDATORY,
    ERR_INIT_CERTS_MANDATORY,
    ERR_INIT_CERTS_EXCLUDE_MCH_SERIAL,
    ERR_UNSUPPORTED_SIGN_TYPE,
    ERR_UNSUPPORTED_ENCRYPT_TYPE,
)
from .errors import DouYinPayInvalidArgumentError
from .crypto.rsa import load_rsa_private_key


KeyLike = Union[str, bytes]


class CertificateProvider(ABC):
    @abstractmethod
    def get_certs(self) -> Dict[str, KeyLike]: ...

    def ensure_ready(self) -> Dict[str, KeyLike]: ...

    def refresh(self) -> Dict[str, KeyLike]: ...

    def refresh_for_serial(self, serial: str) -> Dict[str, KeyLike]:
        certs = self.get_certs()
        if serial and serial in certs:
            return certs
        refreshed = self.refresh()
        return refreshed if refreshed else certs

    def start(self) -> None: ...

    def stop(self) -> None: ...


@dataclass
class DouYinPayConfig:
    mchid: str
    serial: str
    private_key: KeyLike
    certs: Dict[str, KeyLike]
    sign_type: str = SignType.RSA
    encrypt_type: str = EncryptType.AES
    certificate_provider: Optional[CertificateProvider] = None
    base_url: str = DEFAULT_BASE_URL
    base_uri: Optional[str] = None
    max_clock_offset: int = DEFAULT_MAX_CLOCK_OFFSET
    timeout: float = DEFAULT_TIMEOUT
    sdk_agent: Optional[str] = None
    encrypt_key: Optional[str] = None
    http_client: Optional[Any] = None
    on_request: Optional[Callable] = None


def validate_config(config: DouYinPayConfig) -> None:
    if not config.mchid or not isinstance(config.mchid, str) or not config.mchid.strip():
        raise DouYinPayInvalidArgumentError(ERR_INIT_MCHID_MANDATORY)
    if not config.serial or not isinstance(config.serial, str) or not config.serial.strip():
        raise DouYinPayInvalidArgumentError(ERR_INIT_SERIAL_MANDATORY)
    if config.private_key is None:
        raise DouYinPayInvalidArgumentError(ERR_INIT_PRIVATE_KEY_MANDATORY)
    if not isinstance(config.certs, dict):
        raise DouYinPayInvalidArgumentError(ERR_INIT_CERTS_MANDATORY)
    has_provider = config.certificate_provider is not None
    if not has_provider and len(config.certs) == 0:
        raise DouYinPayInvalidArgumentError(ERR_INIT_CERTS_MANDATORY)
    if config.serial in config.certs:
        raise DouYinPayInvalidArgumentError(ERR_INIT_CERTS_EXCLUDE_MCH_SERIAL)
    if config.sign_type != SignType.RSA:
        raise DouYinPayInvalidArgumentError(ERR_UNSUPPORTED_SIGN_TYPE % config.sign_type)
    if config.encrypt_type != EncryptType.AES:
        raise DouYinPayInvalidArgumentError(ERR_UNSUPPORTED_ENCRYPT_TYPE % config.encrypt_type)
    if has_provider and not config.encrypt_key:
        raise DouYinPayInvalidArgumentError("encrypt_key is required for auto certificate mode")
    if config.sign_type == SignType.RSA and config.encrypt_type != EncryptType.AES:
        raise DouYinPayInvalidArgumentError("RSA sign type must pair with AES encrypt type")
    try:
        load_rsa_private_key(config.private_key)
    except Exception as e:
        raise DouYinPayInvalidArgumentError(f"invalid private key: {e}")
