# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Dict, Optional

from . import paths
from .base import Service


class RefundService(Service):
    def create(self, data: Dict[str, Any], **kwargs):
        return self._post(paths.REFUND, data, **kwargs)

    def query_by_out_refund_no(
        self,
        out_refund_no: str,
        mchid: Optional[str] = None,
        appid: Optional[str] = None,
        sp_mchid: Optional[str] = None,
        sub_mchid: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        query = self._params(params, mchid=mchid, appid=appid, sp_mchid=sp_mchid, sub_mchid=sub_mchid)
        path = self._path(paths.REFUND_QUERY_BY_OUT_REFUND_NO, out_refund_no=out_refund_no)
        return self._get(path, params=query, **kwargs)
