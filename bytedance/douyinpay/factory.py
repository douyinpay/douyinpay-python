# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from typing import Optional, Dict, Any

from .config import DouYinPayConfig, KeyLike
from .client import DouyinPayClient
from .constants import SignType, EncryptType, SdkAgentType, DEFAULT_REFRESH_INTERVAL_SEC
from .utils.pem import read_key_data, get_certificate_serial_number, add_certificate
from .certificates import AutoCertificateManager


@dataclass
class AutoClientWithManager:
    client: DouyinPayClient
    certificate_manager: AutoCertificateManager


def _normalize_kwargs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Keep compatibility with older test/examples that used api_base."""
    api_base = kwargs.pop("api_base", None)
    if api_base and "base_url" not in kwargs and "base_uri" not in kwargs:
        kwargs["base_url"] = api_base
    return kwargs


def create_rsa_client(
    mchid: str,
    serial: str,
    private_key: KeyLike,
    platform_certificate: KeyLike,
    platform_serial: Optional[str] = None,
    **kwargs,
) -> DouyinPayClient:
    """Create an RSA client with a local DouyinPay platform certificate.

    This mirrors Go SDK InitClientRSA. The ``serial`` argument is the merchant
    API certificate serial number. When ``platform_certificate`` is a full PEM
    certificate, the platform certificate serial is parsed automatically.
    """
    kwargs = _normalize_kwargs(kwargs)
    cert_pem = read_key_data(platform_certificate)
    if not platform_serial:
        platform_serial = get_certificate_serial_number(cert_pem)
    certs: Dict[str, KeyLike] = {}
    add_certificate(certs, cert_pem, platform_serial)
    user_sign = kwargs.pop("sign_type", None)
    user_enc = kwargs.pop("encrypt_type", None)
    config = DouYinPayConfig(
        mchid=mchid,
        serial=serial,
        private_key=private_key,
        certs=certs,
        sign_type=user_sign if user_sign is not None else SignType.RSA,
        encrypt_type=user_enc if user_enc is not None else EncryptType.AES,
        sdk_agent=kwargs.pop("sdk_agent", SdkAgentType.RSA),
        **kwargs,
    )
    return DouyinPayClient(config)


def create_auto_rsa_client_with_manager(
    mchid: str,
    serial: str,
    private_key: KeyLike,
    encrypt_key: str,
    refresh_interval_sec: int = DEFAULT_REFRESH_INTERVAL_SEC,
    **kwargs,
) -> AutoClientWithManager:
    """Create an RSA client that downloads and refreshes platform certificates.

    This mirrors Go SDK InitAutoClientRSA. The caller does not provide
    ``platform_certificate``; ``encrypt_key`` is used to decrypt downloaded
    platform certificates and callback resources.
    """
    kwargs = _normalize_kwargs(kwargs)
    manager_kwargs = {
        "mchid": mchid,
        "serial": serial,
        "private_key": private_key,
        "encrypt_key": encrypt_key,
        "sign_type": SignType.RSA,
        "encrypt_type": EncryptType.AES,
        "refresh_interval_sec": refresh_interval_sec,
    }
    for k in ("base_url", "base_uri", "max_clock_offset", "timeout", "http_client", "on_request"):
        if k in kwargs:
            manager_kwargs[k] = kwargs[k]
    manager = AutoCertificateManager(**manager_kwargs)
    certs = manager.ensure_ready()
    manager.start()
    user_sign = kwargs.pop("sign_type", None)
    user_enc = kwargs.pop("encrypt_type", None)
    config = DouYinPayConfig(
        mchid=mchid,
        serial=serial,
        private_key=private_key,
        certs=certs,
        sign_type=user_sign if user_sign is not None else SignType.RSA,
        encrypt_type=user_enc if user_enc is not None else EncryptType.AES,
        certificate_provider=manager,
        encrypt_key=encrypt_key,
        sdk_agent=kwargs.pop("sdk_agent", SdkAgentType.AUTO_RSA),
        **kwargs,
    )
    client = DouyinPayClient(config)
    client._certificate_manager = manager
    return AutoClientWithManager(client=client, certificate_manager=manager)


def create_auto_rsa_client(
    mchid: str,
    serial: str,
    private_key: KeyLike,
    encrypt_key: str,
    refresh_interval_sec: int = DEFAULT_REFRESH_INTERVAL_SEC,
    **kwargs,
) -> DouyinPayClient:
    return create_auto_rsa_client_with_manager(
        mchid,
        serial,
        private_key,
        encrypt_key,
        refresh_interval_sec,
        **kwargs,
    ).client


create_client = create_rsa_client
create_auto_client = create_auto_rsa_client
