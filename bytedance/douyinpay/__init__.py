# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

from .callback import CallbackHandler, EncryptedResource, NotifyRequest, parse_callback
from .certificates import AutoCertificateManager, download_platform_certificates
from .client import DouyinPayClient, DouyinPayResponse, PathClient
from .config import CertificateProvider, DouYinPayConfig, KeyLike
from .constants import EncryptType, SdkAgentType, SignType
from .crypto.rsa import load_rsa_private_key, load_rsa_public_key, rsa_encrypt, rsa_sign, rsa_verify
from .errors import (
    DouYinPayAPIError,
    DouYinPayCertificateError,
    DouYinPayError,
    DouYinPayInvalidArgumentError,
    DouYinPaySignatureError,
)
from .factory import (
    AutoClientWithManager,
    create_auto_client,
    create_auto_rsa_client,
    create_auto_rsa_client_with_manager,
    create_client,
    create_rsa_client,
)
from .services import DouyinPayServices, Service
from .version import SDK_VERSION, USER_AGENT, build_sdk_agent

__version__ = SDK_VERSION

__all__ = [
    "__version__",
    "SDK_VERSION",
    "DouyinPayClient",
    "PathClient",
    "DouyinPayResponse",
    "DouYinPayConfig",
    "CertificateProvider",
    "KeyLike",
    "SignType",
    "EncryptType",
    "SdkAgentType",
    "create_rsa_client",
    "create_auto_rsa_client_with_manager",
    "create_auto_rsa_client",
    "AutoClientWithManager",
    "create_client",
    "create_auto_client",
    "AutoCertificateManager",
    "download_platform_certificates",
    "CallbackHandler",
    "parse_callback",
    "NotifyRequest",
    "EncryptedResource",
    "Service",
    "DouyinPayServices",
    "rsa_encrypt",
    "rsa_sign",
    "rsa_verify",
    "load_rsa_private_key",
    "load_rsa_public_key",
    "DouYinPayError",
    "DouYinPayInvalidArgumentError",
    "DouYinPaySignatureError",
    "DouYinPayAPIError",
    "DouYinPayCertificateError",
    "build_sdk_agent",
    "USER_AGENT",
]
