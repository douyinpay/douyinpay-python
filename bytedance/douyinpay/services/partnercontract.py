# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Dict, Optional

from . import paths
from .base import Service


class PartnerContractService(Service):
    def query_contract(
        self,
        plan_id: Any,
        out_contract_code: str,
        sp_mchid: Optional[str] = None,
        sub_mchid: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        path = self._path(paths.PARTNER_QUERY_CONTRACT, plan_id=plan_id, out_contract_code=out_contract_code)
        query = self._params(params, sp_mchid=sp_mchid, sub_mchid=sub_mchid)
        return self._get(path, params=query, **kwargs)

    def terminate_contract(
        self,
        plan_id: Any,
        out_contract_code: str,
        data: Dict[str, Any],
        **kwargs,
    ):
        path = self._path(paths.PARTNER_TERMINATE_CONTRACT, plan_id=plan_id, out_contract_code=out_contract_code)
        return self._post(path, data, **kwargs)
