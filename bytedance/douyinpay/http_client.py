# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

import json as _json
from typing import Any, Dict, Optional, Union
from collections.abc import Callable

import httpx

from .config import DouYinPayConfig, validate_config
from .constants import Headers, EncryptType, SignType
from .errors import DouYinPayAPIError
from .version import USER_AGENT, build_sdk_agent
from .utils.http import normalize_base_url, join_url, append_query, request_target_from_url, buffer_to_str
from .utils.pem import read_key_data
from .crypto.rsa import load_rsa_private_key
from .crypto.sm2 import load_sm2_private_key
from .signer import sign_request, verify_response


def _build_body(body: Optional[Union[str, bytes]], json_data: Optional[Any]) -> str:
    if body is not None:
        return buffer_to_str(body)
    if json_data is not None:
        return _json.dumps(json_data, ensure_ascii=False, separators=(",", ":"))
    return ""


class HttpClient:
    def __init__(self, config: DouYinPayConfig):
        validate_config(config)
        self.config = config
        base = config.base_uri or config.base_url
        self.base_url = normalize_base_url(base)
        if config.sign_type == SignType.RSA:
            self._private_key = load_rsa_private_key(config.private_key)
        else:
            self._private_key = load_sm2_private_key(config.private_key)
        self._sign_type = config.sign_type
        self._encrypt_type = config.encrypt_type
        self._owns_client = config.http_client is None
        self._client = config.http_client or httpx.Client(timeout=config.timeout)
        self._closed = False

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def _get_current_certs(self) -> Dict[str, Any]:
        certs = dict(self.config.certs or {})
        if self.config.certificate_provider is not None:
            try:
                provider_certs = self.config.certificate_provider.get_certs()
                if provider_certs:
                    certs.update(provider_certs)
            except Exception:
                pass
        return certs

    def request(
        self,
        method: str,
        path: str,
        json: Optional[Any] = None,
        params: Optional[Any] = None,
        body: Optional[Union[str, bytes]] = None,
        headers: Optional[Dict[str, str]] = None,
        files: Optional[Any] = None,
        skip_verify: bool = False,
        on_request: Optional[Callable] = None,
        response_type: str = "json",
        **kwargs,
    ):
        is_multipart = files is not None
        if is_multipart:
            sign_body = ""
            content = None
        else:
            content = _build_body(body, json)
            sign_body = content
        url = append_query(join_url(self.base_url, path), params)
        request_target = request_target_from_url(url)
        signed = sign_request(
            method.upper(),
            request_target,
            sign_body,
            self.config.mchid,
            self.config.serial,
            self._private_key,
            self._sign_type,
        )
        request_headers = {
            Headers.Accept: "application/json, text/plain, application/x-gzip, application/pdf, image/png, image/*;q=0.5",
            Headers.UserAgent: USER_AGENT,
        }
        if not is_multipart:
            request_headers[Headers.ContentType] = "application/json; charset=utf-8"
        if headers:
            request_headers.update(headers)
        request_headers.update(signed.headers)
        if self.config.sdk_agent:
            request_headers[Headers.SdkAgent] = build_sdk_agent(self.config.sdk_agent, self.config.mchid)
        request_callback = on_request or self.config.on_request
        if request_callback:
            request_callback({
                "method": method.upper(),
                "path": path,
                "url": url,
                "requestTarget": request_target,
                "headers": request_headers,
                "body": sign_body,
            })
        send_kwargs: Dict[str, Any] = {}
        if is_multipart:
            send_kwargs["files"] = files
            if "data" not in kwargs:
                if json is not None:
                    meta_str = _json.dumps(json, ensure_ascii=False, separators=(",", ":")) if isinstance(json, (dict, list)) else str(json)
                    send_kwargs["data"] = {"meta": meta_str}
                elif body is not None:
                    send_kwargs["content"] = body
        else:
            send_kwargs["content"] = content.encode("utf-8") if content is not None else b""
        send_kwargs.update(kwargs)
        resp = self._client.request(
            method=method.upper(),
            url=url,
            headers=request_headers,
            **send_kwargs,
        )
        if resp.status_code >= 400:
            raise DouYinPayAPIError(
                f"HTTP {resp.status_code}",
                status_code=resp.status_code,
                response_body=resp.text,
            )
        if not skip_verify:
            resp_headers = dict(resp.headers)
            current_certs = self._get_current_certs()
            verify_response(
                resp_headers,
                resp.content,
                current_certs,
                self._sign_type,
                self._encrypt_type,
                self.config.max_clock_offset,
            )
        if response_type == "content":
            data: Any = resp.content
        elif response_type == "text":
            data = resp.text
        else:
            try:
                data = resp.json()
            except Exception:
                data = resp.text
        from .client import DouyinPayResponse
        return DouyinPayResponse(
            status_code=resp.status_code,
            data=data,
            headers=dict(resp.headers),
        )

    def get(self, path: str, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path: str, json: Optional[Any] = None, **kwargs):
        return self.request("POST", path, json=json, **kwargs)

    def put(self, path: str, json: Optional[Any] = None, **kwargs):
        return self.request("PUT", path, json=json, **kwargs)

    def patch(self, path: str, json: Optional[Any] = None, **kwargs):
        return self.request("PATCH", path, json=json, **kwargs)

    def delete(self, path: str, **kwargs):
        return self.request("DELETE", path, **kwargs)
