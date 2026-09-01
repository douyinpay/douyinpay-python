# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Dict, Optional

from .base import Service


class PayScoreService(Service):
    """Generic PayScore API entry for merchant-supplied paths and params."""

    def request(
        self,
        method: str,
        path: str,
        json: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        path_params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        api_path = self._path(path, **(path_params or {}))
        return self.client.request(method, api_path, json=json, params=params, **kwargs)

    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        path_params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        return self.request("GET", path, params=params, path_params=path_params, **kwargs)

    def post(
        self,
        path: str,
        json: Optional[Any] = None,
        path_params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        return self.request("POST", path, json={} if json is None else json, path_params=path_params, **kwargs)

    def put(
        self,
        path: str,
        json: Optional[Any] = None,
        path_params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        return self.request("PUT", path, json={} if json is None else json, path_params=path_params, **kwargs)

    def patch(
        self,
        path: str,
        json: Optional[Any] = None,
        path_params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        return self.request("PATCH", path, json={} if json is None else json, path_params=path_params, **kwargs)

    def delete(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        path_params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        return self.request("DELETE", path, params=params, path_params=path_params, **kwargs)


class PartnerPayScoreService(PayScoreService):
    """Generic partner PayScore API entry for merchant-supplied paths and params."""
