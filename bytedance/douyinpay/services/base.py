# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Dict, Optional
from urllib.parse import quote


class Service:
    """Thin generic API wrapper over DouyinPayClient."""

    def __init__(self, client):
        self.client = client

    def _path(self, template: str, **path_params: Any) -> str:
        path = template
        for key, value in path_params.items():
            if value is None or value == "":
                raise ValueError(f"{key} is required")
            path = path.replace("{" + key + "}", quote(str(value), safe=""))
        return path

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

    def path(self, path: str):
        return self.client.path(path)
