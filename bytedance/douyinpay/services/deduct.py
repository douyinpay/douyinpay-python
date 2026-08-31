# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Dict, Optional

from . import paths
from .base import Service
from .pay import TransactionService


class DeductService(TransactionService):
    prepay_path = paths.DEDUCT

    def deduct(self, data: Dict[str, Any], **kwargs):
        return self._post(paths.DEDUCT, data, **kwargs)

    def pay_apply(self, data: Dict[str, Any], **kwargs):
        return self._post(paths.DEDUCT, data, **kwargs)

    def deduct_notify(self, data: Dict[str, Any], **kwargs):
        return self._post(paths.DEDUCT_NOTIFY, data, **kwargs)


class PartnerDeductService(Service):
    def contract_schedule(self, contract_id: str, data: Dict[str, Any], **kwargs):
        return self._post(self._path(paths.PARTNER_CONTRACT_SCHEDULE, contract_id=contract_id), data, **kwargs)

    def contract_schedule_query(
        self,
        contract_id: str,
        sp_mchid: Optional[str] = None,
        sub_mchid: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        query = self._params(params, sp_mchid=sp_mchid, sub_mchid=sub_mchid)
        return self._get(self._path(paths.PARTNER_CONTRACT_SCHEDULE_QUERY, contract_id=contract_id), params=query, **kwargs)
