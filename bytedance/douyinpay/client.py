# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from typing import Dict, Generic, TypeVar, Any, Optional

T = TypeVar("T")


@dataclass
class DouyinPayResponse(Generic[T]):
    status_code: int
    data: T
    headers: Dict[str, str]


class DouyinPayClient:
    def __init__(self, config):
        from .http_client import HttpClient
        self._http = HttpClient(config)
        self.config = config
        self._certificate_manager: Any = None

    @property
    def certificate_manager(self):
        return self._certificate_manager

    def get_client(self, api_path: Optional[str] = None):
        return PathClient(self._http, api_path) if api_path else self._http

    def path(self, api_path: str) -> "PathClient":
        return self.get_client(api_path)

    def close(self) -> None:
        if self._certificate_manager is not None:
            try:
                self._certificate_manager.stop()
            except Exception:
                pass
        self._http.close()

    def __enter__(self) -> "DouyinPayClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


class PathClient:
    def __init__(self, http, path: str):
        self._http = http
        self.path = path

    def get(self, params=None, **kwargs):
        return self._http.get(self.path, params=params, **kwargs)

    def post(self, json=None, files=None, **kwargs):
        return self._http.post(self.path, json=json, files=files, **kwargs)

    def put(self, json=None, files=None, **kwargs):
        return self._http.put(self.path, json=json, files=files, **kwargs)

    def patch(self, json=None, files=None, **kwargs):
        return self._http.patch(self.path, json=json, files=files, **kwargs)

    def delete(self, **kwargs):
        return self._http.delete(self.path, **kwargs)
