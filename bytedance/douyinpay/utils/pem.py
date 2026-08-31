# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Union, Dict, Optional

from cryptography import x509


KeyLike = Union[str, bytes]


def read_key_data(key_data: KeyLike) -> bytes:
    if isinstance(key_data, bytes):
        return key_data
    if isinstance(key_data, str):
        stripped = key_data.strip()
        if os.path.isfile(stripped):
            with open(stripped, "rb") as f:
                return f.read()
        return stripped.encode("utf-8")
    raise TypeError("key_data must be str or bytes")


def is_pem_certificate(data: KeyLike) -> bool:
    raw = read_key_data(data)
    try:
        text = raw.decode("utf-8", errors="ignore")
    except Exception:
        return False
    return "-----BEGIN CERTIFICATE-----" in text


def get_certificate_serial_number(pem_str: KeyLike) -> str:
    data = read_key_data(pem_str)
    cert = x509.load_pem_x509_certificate(data)
    serial = cert.serial_number
    hex_str = format(serial, "X")
    if len(hex_str) % 2 == 1:
        hex_str = "0" + hex_str
    return hex_str.upper()


def add_certificate(certs: Dict[str, bytes], cert_pem: KeyLike, serial: Optional[str] = None) -> Dict[str, bytes]:
    pem_bytes = read_key_data(cert_pem)
    if serial:
        certs[serial] = pem_bytes
    try:
        parsed_serial = get_certificate_serial_number(pem_bytes)
        certs[parsed_serial] = pem_bytes
    except Exception:
        pass
    return certs
