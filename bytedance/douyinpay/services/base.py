# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Dict, Optional
from urllib.parse import quote


class Service:
    """Thin business API wrapper over DouyinPayClient."""

    def __init__(self, client):
        self.client = client

    def _path(self, template: str, **path_params: Any) -> str:
        path = template
        for key, value in path_params.items():
            if value is None or value == "":
                raise ValueError(f"{key} is required")
            path = path.replace("{" + key + "}", quote(str(value), safe=""))
        return path

    def _params(self, params: Optional[Dict[str, Any]] = None, **values: Any) -> Dict[str, Any]:
        merged: Dict[str, Any] = {}
        if params:
            merged.update(params)
        for key, value in values.items():
            if value is not None:
                merged[key] = value
        return merged

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None, **kwargs):
        return self.client.path(path).get(params=params, **kwargs)

    def _post(self, path: str, data: Optional[Dict[str, Any]] = None, **kwargs):
        return self.client.path(path).post(data or {}, **kwargs)
