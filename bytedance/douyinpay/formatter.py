# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

import time
import secrets
import string
from typing import Union

from .constants import (
    AUTHORIZATION_TYPE,
    DEFAULT_NONCE_SIZE,
)


def generate_nonce(size: int = DEFAULT_NONCE_SIZE) -> str:
    alphabet = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(size))


def generate_timestamp() -> int:
    return int(time.time())


def build_authorization(
    mchid: str,
    nonce: str,
    signature: str,
    timestamp: int,
    serial: str,
) -> str:
    return (
        f'{AUTHORIZATION_TYPE} mchid="{mchid}",serial_no="{serial}",'
        f'timestamp="{timestamp}",nonce_str="{nonce}",signature="{signature}"'
    )


def build_request_sign_message(
    method: str,
    request_target: str,
    timestamp: int,
    nonce: str,
    body: Union[str, bytes] = "",
) -> Union[str, bytes]:
    if body is None:
        body = ""
    if isinstance(body, bytes):
        return (
            method.upper().encode("ascii") + b"\n"
            + request_target.encode("utf-8") + b"\n"
            + str(timestamp).encode("ascii") + b"\n"
            + nonce.encode("ascii") + b"\n"
            + body + b"\n"
        )
    return f"{method.upper()}\n{request_target}\n{timestamp}\n{nonce}\n{body}\n"


def build_response_verify_message(
    timestamp: int,
    nonce: str,
    body: Union[str, bytes] = "",
) -> Union[str, bytes]:
    if body is None:
        body = ""
    if isinstance(body, bytes):
        return (
            str(timestamp).encode("ascii") + b"\n"
            + nonce.encode("ascii") + b"\n"
            + body + b"\n"
        )
    return f"{timestamp}\n{nonce}\n{body}\n"
