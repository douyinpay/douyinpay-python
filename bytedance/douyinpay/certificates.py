# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

import threading
from dataclasses import dataclass, replace
from typing import Dict, List, Optional

from .config import DouYinPayConfig, CertificateProvider, KeyLike
from .constants import (
    GET_PLATFORM_CERTS_PATH,
    DEFAULT_REFRESH_INTERVAL_SEC,
)
from .errors import DouYinPayCertificateError
from .utils.pem import add_certificate
from .crypto.aes import aes_decrypt


@dataclass
class DownloadedCertificate:
    serial_no: str
    certificate: str
    effective_time: Optional[str] = None
    expire_time: Optional[str] = None


def download_platform_certificates(
    config: DouYinPayConfig,
    verify_response: bool = False,
) -> List[DownloadedCertificate]:
    from .http_client import HttpClient

    if not verify_response:
        bootstrap_certs: Dict[str, KeyLike] = {"_bootstrap": ""}
    else:
        bootstrap_certs = None
    temp_config = replace(
        config,
        certs=bootstrap_certs if bootstrap_certs is not None else config.certs,
    )
    client = HttpClient(temp_config)
    resp = client.get(GET_PLATFORM_CERTS_PATH, skip_verify=not verify_response)
    if not isinstance(resp.data, dict):
        raise DouYinPayCertificateError(f"unexpected response type: {type(resp.data)}")
    certificates: List[DownloadedCertificate] = []
    for item in resp.data.get("certificates", []):
        encrypted = item.get("encrypt_certificate") or {}
        plaintext = aes_decrypt(
            encrypted["cipher_text"],
            config.encrypt_key or "",
            encrypted.get("nonce", ""),
            encrypted.get("associated_data", ""),
        )
        certificates.append(DownloadedCertificate(
            serial_no=item.get("cert_no") or item.get("serial_no") or "",
            certificate=plaintext,
            effective_time=item.get("effective_time"),
            expire_time=item.get("expire_time"),
        ))
    return certificates


class AutoCertificateManager(CertificateProvider):
    def __init__(
        self,
        mchid: str,
        serial: str,
        private_key: KeyLike,
        encrypt_key: str,
        sign_type: str,
        encrypt_type: str,
        refresh_interval_sec: int = DEFAULT_REFRESH_INTERVAL_SEC,
        base_url: Optional[str] = None,
        base_uri: Optional[str] = None,
        max_clock_offset: int = 300,
        timeout: float = 30.0,
        http_client=None,
        on_request=None,
    ):
        self._mchid = mchid
        self._serial = serial
        self._private_key = private_key
        self._encrypt_key = encrypt_key
        self._sign_type = sign_type
        self._encrypt_type = encrypt_type
        self._refresh_interval_sec = refresh_interval_sec
        self._base_url = base_url
        self._base_uri = base_uri
        self._max_clock_offset = max_clock_offset
        self._timeout = timeout
        self._custom_http_client = http_client
        self._on_request = on_request
        self._lock = threading.Lock()
        self._refreshing: Optional[threading.Event] = None
        self._timer: Optional[threading.Timer] = None
        self._certs: Dict[str, KeyLike] = {}

    def _build_config(self, certs: Dict[str, KeyLike]) -> DouYinPayConfig:
        return DouYinPayConfig(
            mchid=self._mchid,
            serial=self._serial,
            private_key=self._private_key,
            certs=certs,
            sign_type=self._sign_type,
            encrypt_type=self._encrypt_type,
            base_url=self._base_url or "https://api.douyinpay.com",
            base_uri=self._base_uri,
            max_clock_offset=self._max_clock_offset,
            timeout=self._timeout,
            encrypt_key=self._encrypt_key,
            http_client=self._custom_http_client,
            on_request=self._on_request,
        )

    def get_certs(self) -> Dict[str, KeyLike]:
        with self._lock:
            return dict(self._certs)

    def ensure_ready(self) -> Dict[str, KeyLike]:
        with self._lock:
            if self._certs:
                return dict(self._certs)
        return self.refresh(verify_response=False)

    def refresh_for_serial(self, serial: str) -> Dict[str, KeyLike]:
        if not serial:
            return self.get_certs()
        with self._lock:
            if serial in self._certs:
                return dict(self._certs)
        return self.refresh(verify_response=True)

    def refresh(self, verify_response: bool = True) -> Dict[str, KeyLike]:
        self._lock.acquire()
        if self._refreshing is not None:
            event = self._refreshing
            self._lock.release()
            event.wait()
            with self._lock:
                return dict(self._certs)
        self._refreshing = threading.Event()
        self._lock.release()
        try:
            if verify_response:
                current_certs = self.get_certs()
                cfg = self._build_config(current_certs)
            else:
                cfg = self._build_config({"_bootstrap": ""})
            downloaded = download_platform_certificates(cfg, verify_response=verify_response)
            new_certs: Dict[str, KeyLike] = {}
            for cert in downloaded:
                add_certificate(new_certs, cert.certificate, cert.serial_no)
            with self._lock:
                self._certs = new_certs
                return dict(new_certs)
        finally:
            with self._lock:
                event = self._refreshing
                self._refreshing = None
            if event is not None:
                event.set()

    def _tick(self):
        try:
            self.refresh(verify_response=True)
        except Exception:
            pass
        self._schedule_next()

    def _schedule_next(self):
        if self._refresh_interval_sec <= 0:
            return
        self._timer = threading.Timer(self._refresh_interval_sec, self._tick)
        self._timer.daemon = True
        self._timer.start()

    def start(self):
        if self._refresh_interval_sec <= 0:
            return
        with self._lock:
            if self._timer is not None:
                return
        self._schedule_next()

    def stop(self):
        with self._lock:
            t = self._timer
            self._timer = None
        if t is not None:
            t.cancel()
