# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Dict, Optional

from . import paths
from .pay import TransactionService


class PartnerTransactionService(TransactionService):
    close_path = paths.PARTNER_CLOSE_ORDER
    query_by_id_path = paths.PARTNER_QUERY_ORDER_BY_ID
    query_by_out_trade_no_path = paths.PARTNER_QUERY_ORDER_BY_OUT_TRADE_NO

    def close_order(
        self,
        out_trade_no: str,
        sp_mchid: Optional[str] = None,
        sub_mchid: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        body = dict(data or {})
        if sp_mchid is not None:
            body["sp_mchid"] = sp_mchid
        if sub_mchid is not None:
            body["sub_mchid"] = sub_mchid
        return self._post(self._path(self.close_path, out_trade_no=out_trade_no), body, **kwargs)

    def query_order_by_id(
        self,
        transaction_id: str,
        sp_mchid: Optional[str] = None,
        sub_mchid: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        query = self._params(params, sp_mchid=sp_mchid, sub_mchid=sub_mchid)
        return self._get(self._path(self.query_by_id_path, transaction_id=transaction_id), params=query, **kwargs)

    def query_order_by_out_trade_no(
        self,
        out_trade_no: str,
        sp_mchid: Optional[str] = None,
        sub_mchid: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        query = self._params(params, sp_mchid=sp_mchid, sub_mchid=sub_mchid)
        return self._get(self._path(self.query_by_out_trade_no_path, out_trade_no=out_trade_no), params=query, **kwargs)


class PartnerAppPayService(PartnerTransactionService):
    prepay_path = paths.PARTNER_APP_PREPAY


class PartnerH5PayService(PartnerTransactionService):
    prepay_path = paths.PARTNER_H5_PREPAY


class PartnerJsapiPayService(PartnerTransactionService):
    prepay_path = paths.PARTNER_JSAPI_PREPAY


class PartnerNativePayService(PartnerTransactionService):
    prepay_path = paths.PARTNER_NATIVE_PREPAY


class PartnerContractPayService(PartnerTransactionService):
    def contract_order(self, data: Dict[str, Any], **kwargs):
        return self._post(paths.PARTNER_CONTRACT_ORDER, data, **kwargs)

    def pay_apply(self, data: Dict[str, Any], **kwargs):
        return self._post(paths.PARTNER_PAY_APPLY, data, **kwargs)
