# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Dict, Optional

from . import paths
from .base import Service


class TransactionService(Service):
    prepay_path = ""
    close_path = paths.CLOSE_ORDER
    query_by_id_path = paths.QUERY_ORDER_BY_ID
    query_by_out_trade_no_path = paths.QUERY_ORDER_BY_OUT_TRADE_NO

    def prepay(self, data: Dict[str, Any], **kwargs):
        return self._post(self.prepay_path, data, **kwargs)

    def close_order(
        self,
        out_trade_no: str,
        mchid: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        body = dict(data or {})
        if mchid is not None:
            body["mchid"] = mchid
        return self._post(self._path(self.close_path, out_trade_no=out_trade_no), body, **kwargs)

    def query_order_by_id(
        self,
        transaction_id: str,
        mchid: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        query = self._params(params, mchid=mchid)
        return self._get(self._path(self.query_by_id_path, transaction_id=transaction_id), params=query, **kwargs)

    def query_order_by_out_trade_no(
        self,
        out_trade_no: str,
        mchid: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        query = self._params(params, mchid=mchid)
        return self._get(self._path(self.query_by_out_trade_no_path, out_trade_no=out_trade_no), params=query, **kwargs)


class AppPayService(TransactionService):
    prepay_path = paths.APP_PREPAY


class H5PayService(TransactionService):
    prepay_path = paths.H5_PREPAY


class JsapiPayService(TransactionService):
    prepay_path = paths.JSAPI_PREPAY


class NativePayService(TransactionService):
    prepay_path = paths.NATIVE_PREPAY


class ContractOrderPayService(TransactionService):
    prepay_path = paths.CONTRACT_ORDER_PREPAY


class CreditContractOrderPayService(TransactionService):
    prepay_path = paths.CREDIT_CONTRACT_ORDER_PREPAY
