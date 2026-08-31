# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Dict, Optional

from . import paths
from .base import Service


class PayScoreService(Service):
    def create_service_order(self, data: Dict[str, Any], **kwargs):
        return self._post(paths.PAYSCORE_CREATE_SERVICE_ORDER, data, **kwargs)

    def complete_service_order(self, data: Dict[str, Any], **kwargs):
        return self._post(paths.PAYSCORE_COMPLETE_SERVICE_ORDER, data, **kwargs)

    def query_service_order(self, params: Optional[Dict[str, Any]] = None, **kwargs):
        return self._get(paths.PAYSCORE_QUERY_SERVICE_ORDER, params=params, **kwargs)

    def cancel_service_order(self, data: Dict[str, Any], **kwargs):
        return self._post(paths.PAYSCORE_CANCEL_SERVICE_ORDER, data, **kwargs)

    def modify_amount(self, data: Dict[str, Any], **kwargs):
        return self._post(paths.PAYSCORE_MODIFY_SERVICE_ORDER, data, **kwargs)

    def synchronize_service_order_info(self, out_order_no: str, data: Dict[str, Any], **kwargs):
        return self._post(self._path(paths.PAYSCORE_SYNC_SERVICE_ORDER, out_order_no=out_order_no), data, **kwargs)

    def service_order_pay(self, out_order_no: str, data: Dict[str, Any], **kwargs):
        return self._post(self._path(paths.PAYSCORE_SERVICE_ORDER_PAY, out_order_no=out_order_no), data, **kwargs)

    def credit_sign_apply(self, data: Dict[str, Any], **kwargs):
        return self._post(paths.PAYSCORE_CREDIT_SIGN_APPLY, data, **kwargs)

    def credit_sign_query(self, authorization_code: str, params: Optional[Dict[str, Any]] = None, **kwargs):
        path = self._path(paths.PAYSCORE_CREDIT_SIGN_QUERY, authorization_code=authorization_code)
        return self._get(path, params=params, **kwargs)

    def close_credit_service(self, authorization_code: str, data: Optional[Dict[str, Any]] = None, **kwargs):
        path = self._path(paths.PAYSCORE_CLOSE_CREDIT_SERVICE, authorization_code=authorization_code)
        return self._post(path, data, **kwargs)


class PartnerPayScoreService(Service):
    def create_service_order(self, data: Dict[str, Any], **kwargs):
        return self._post(paths.PARTNER_PAYSCORE_CREATE_SERVICE_ORDER, data, **kwargs)

    def complete_service_order(self, data: Dict[str, Any], **kwargs):
        return self._post(paths.PARTNER_PAYSCORE_COMPLETE_SERVICE_ORDER, data, **kwargs)

    def query_service_order(self, params: Optional[Dict[str, Any]] = None, **kwargs):
        return self._get(paths.PARTNER_PAYSCORE_QUERY_SERVICE_ORDER, params=params, **kwargs)

    def cancel_service_order(self, data: Dict[str, Any], **kwargs):
        return self._post(paths.PARTNER_PAYSCORE_CANCEL_SERVICE_ORDER, data, **kwargs)

    def modify_amount(self, data: Dict[str, Any], **kwargs):
        return self._post(paths.PARTNER_PAYSCORE_MODIFY_SERVICE_ORDER, data, **kwargs)

    def synchronize_service_order_info(self, out_order_no: str, data: Dict[str, Any], **kwargs):
        path = self._path(paths.PARTNER_PAYSCORE_SYNC_SERVICE_ORDER, out_order_no=out_order_no)
        return self._post(path, data, **kwargs)

    def credit_sign_apply(self, data: Dict[str, Any], **kwargs):
        return self._post(paths.PARTNER_PAYSCORE_CREDIT_SIGN_APPLY, data, **kwargs)

    def credit_sign_query(self, authorization_code: str, params: Optional[Dict[str, Any]] = None, **kwargs):
        path = self._path(paths.PARTNER_PAYSCORE_CREDIT_SIGN_QUERY, authorization_code=authorization_code)
        return self._get(path, params=params, **kwargs)

    def close_credit_service(self, authorization_code: str, data: Optional[Dict[str, Any]] = None, **kwargs):
        path = self._path(paths.PARTNER_PAYSCORE_CLOSE_CREDIT_SERVICE, authorization_code=authorization_code)
        return self._post(path, data, **kwargs)
