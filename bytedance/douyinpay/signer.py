# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

import time
from dataclasses import dataclass
from typing import Dict, Any, Optional, Union

from .constants import (
    SignType,
    Headers,
    DEFAULT_MAX_CLOCK_OFFSET,
    ERR_UNSUPPORTED_SIGN_TYPE,
    ERR_RES_HEADERS_INCOMPLETE,
    ERR_RES_TIMESTAMP_OFFSET,
    ERR_RES_PLATFORM_SERIAL_NOT_FOUND,
    ERR_RES_SIGNATURE_VERIFY_FAILED,
)
from .errors import DouYinPaySignatureError, DouYinPayCertificateSerialNotFound, DouYinPayError
from .formatter import (
    generate_nonce,
    generate_timestamp,
    build_authorization,
    build_request_sign_message,
    build_response_verify_message,
)
from .utils.http import header_value
from .crypto.rsa import rsa_sign, rsa_verify, load_rsa_public_key


@dataclass
class SignedRequest:
    headers: Dict[str, str]
    nonce: str
    timestamp: int
    signature: str
    message: str


def create_signer(sign_type: str, private_key=None, public_key=None):
    from .crypto.rsa import RsaSigner
    if sign_type == SignType.RSA:
        return RsaSigner(private_key=private_key, public_key=public_key)
    raise DouYinPayError(ERR_UNSUPPORTED_SIGN_TYPE % sign_type)


def sign_request(
    method: str,
    request_target: str,
    body: str,
    mchid: str,
    serial: str,
    private_key,
    sign_type: str = SignType.RSA,
) -> SignedRequest:
    nonce = generate_nonce()
    timestamp = generate_timestamp()
    message = build_request_sign_message(method, request_target, timestamp, nonce, body or "")

    if sign_type == SignType.RSA:
        signature = rsa_sign(message, private_key)
    else:
        raise DouYinPayError(ERR_UNSUPPORTED_SIGN_TYPE % sign_type)

    authorization = build_authorization(mchid, nonce, signature, timestamp, serial)
    headers = {
        Headers.Authorization: authorization,
    }
    return SignedRequest(
        headers=headers,
        nonce=nonce,
        timestamp=timestamp,
        signature=signature,
        message=message,
    )


def _load_public_key_from_cert(cert_pem, sign_type: str):
    if sign_type == SignType.RSA:
        return load_rsa_public_key(cert_pem)
    raise DouYinPayError(ERR_UNSUPPORTED_SIGN_TYPE % sign_type)


def verify_response(
    headers: Dict[str, Any],
    body: Union[str, bytes],
    platform_certs: Dict[str, Any],
    sign_type: str = SignType.RSA,
    encrypt_type: Optional[str] = None,
    max_clock_offset: int = DEFAULT_MAX_CLOCK_OFFSET,
) -> None:
    ts = header_value(headers, Headers.Timestamp)
    nonce = header_value(headers, Headers.Nonce)
    signature = header_value(headers, Headers.Signature)
    serial = header_value(headers, Headers.Serial)
    if not ts or not nonce or not signature or not serial:
        raise DouYinPaySignatureError(ERR_RES_HEADERS_INCOMPLETE)
    try:
        ts_int = int(ts)
    except (TypeError, ValueError):
        raise DouYinPaySignatureError(ERR_RES_HEADERS_INCOMPLETE)
    offset = abs(time.time() - ts_int)
    if offset > max_clock_offset:
        raise DouYinPaySignatureError(ERR_RES_TIMESTAMP_OFFSET % max_clock_offset)
    if serial not in platform_certs:
        raise DouYinPayCertificateSerialNotFound(serial, ERR_RES_PLATFORM_SERIAL_NOT_FOUND % serial)
    cert_pem = platform_certs[serial]
    public_key = _load_public_key_from_cert(cert_pem, sign_type)
    message = build_response_verify_message(ts_int, nonce, body or "")
    if sign_type == SignType.RSA:
        ok = rsa_verify(message, signature, public_key)
    else:
        raise DouYinPayError(ERR_UNSUPPORTED_SIGN_TYPE % sign_type)
    if not ok:
        raise DouYinPaySignatureError(ERR_RES_SIGNATURE_VERIFY_FAILED)
