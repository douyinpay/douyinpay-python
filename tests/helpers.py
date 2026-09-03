# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple, Union

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from bytedance.douyinpay.utils.pem import get_certificate_serial_number


def make_rsa_key_and_cert(common_name: str = "test-rsa") -> Tuple[bytes, bytes]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow() - timedelta(minutes=1))
        .not_valid_after(datetime.utcnow() + timedelta(days=3650))
        .sign(key, hashes.SHA256())
    )
    key_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    return key_pem, cert_pem


def write_pem(tmp_path: Path, name: str, data: Union[str, bytes]) -> str:
    raw = data.encode("utf-8") if isinstance(data, str) else data
    path = tmp_path / name
    path.write_bytes(raw)
    return str(path)


MCH_PRIV, CERT_PEM = make_rsa_key_and_cert()
CERT_PEM_STR = CERT_PEM.decode("utf-8")
PLAT_SERIAL = get_certificate_serial_number(CERT_PEM)
