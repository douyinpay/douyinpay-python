# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

from .version import SDK_VERSION, build_sdk_agent, USER_AGENT
from .version import SDK_VERSION as __version__
from .client import DouyinPayClient, PathClient, DouyinPayResponse
from .config import DouYinPayConfig, CertificateProvider, KeyLike
from .constants import SignType, EncryptType, SdkAgentType
from .factory import (
    create_rsa_client,
    create_auto_rsa_client_with_manager,
    create_auto_rsa_client,
    create_sm2_client,
    create_auto_sm2_client_with_manager,
    create_auto_sm2_client,
    AutoClientWithManager,
    create_client,
    create_auto_client,
)
from .certificates import AutoCertificateManager, download_platform_certificates
from .callback import CallbackHandler, parse_callback, NotifyRequest, EncryptedResource
from .crypto.rsa import rsa_encrypt, rsa_sign, rsa_verify, load_rsa_private_key, load_rsa_public_key
from .crypto.sm2 import sm2_encrypt, sm2_sign, sm2_verify, load_sm2_private_key, load_sm2_public_key
from .errors import (
    DouYinPayError,
    DouYinPayInvalidArgumentError,
    DouYinPaySignatureError,
    DouYinPayAPIError,
    DouYinPayCertificateError,
)

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
    "create_sm2_client",
    "create_auto_sm2_client_with_manager",
    "create_auto_sm2_client",
    "AutoClientWithManager",
    "create_client",
    "create_auto_client",
    "AutoCertificateManager",
    "download_platform_certificates",
    "CallbackHandler",
    "parse_callback",
    "NotifyRequest",
    "EncryptedResource",
    "rsa_encrypt",
    "rsa_sign",
    "rsa_verify",
    "load_rsa_private_key",
    "load_rsa_public_key",
    "sm2_encrypt",
    "sm2_sign",
    "sm2_verify",
    "load_sm2_private_key",
    "load_sm2_public_key",
    "DouYinPayError",
    "DouYinPayInvalidArgumentError",
    "DouYinPaySignatureError",
    "DouYinPayAPIError",
    "DouYinPayCertificateError",
    "build_sdk_agent",
    "USER_AGENT",
]
