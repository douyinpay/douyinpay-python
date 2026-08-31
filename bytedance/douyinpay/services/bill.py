# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Dict, Optional

from . import paths
from .base import Service


class BillService(Service):
    def apply_bill(self, params: Optional[Dict[str, Any]] = None, **kwargs):
        return self._get(paths.BILL_APPLY, params=params, **kwargs)

    def apply_fund_flow_bill(self, params: Optional[Dict[str, Any]] = None, **kwargs):
        return self._get(paths.FUND_FLOW_BILL, params=params, **kwargs)

    def apply_split_bill(self, params: Optional[Dict[str, Any]] = None, **kwargs):
        return self._get(paths.SPLIT_BILL, params=params, **kwargs)


class PartnerBillService(Service):
    def apply_trade_bill(self, params: Optional[Dict[str, Any]] = None, **kwargs):
        return self._get(paths.TRADE_BILL, params=params, **kwargs)

    def apply_fund_flow_bill(self, params: Optional[Dict[str, Any]] = None, **kwargs):
        return self._get(paths.FUND_FLOW_BILL, params=params, **kwargs)

    def apply_split_bill(self, params: Optional[Dict[str, Any]] = None, **kwargs):
        return self._get(paths.SPLIT_BILL, params=params, **kwargs)
