# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bytedance.douyinpay.client import DouyinPayClient
from bytedance.douyinpay.services import DouyinPayServices, Service


class FakePathClient:
    def __init__(self, owner, path):
        self.owner = owner
        self.path = path

    def get(self, params=None, **kwargs):
        return self.owner.record("GET", self.path, params=params, **kwargs)

    def post(self, json=None, files=None, **kwargs):
        return self.owner.record("POST", self.path, json=json, files=files, **kwargs)


class FakeClient:
    def __init__(self):
        self.calls = []

    def path(self, path):
        return FakePathClient(self, path)

    def request(self, method, path, **kwargs):
        return self.record(method, path, **kwargs)

    def record(self, method, path, **kwargs):
        call = {"method": method, "path": path, **kwargs}
        self.calls.append(call)
        return call


def test_client_services_property_builds_thin_service_once():
    client = object.__new__(DouyinPayClient)
    client._services = None

    services = client.services

    assert isinstance(services, DouyinPayServices)
    assert services.client is client
    assert client.services is services


def test_client_request_delegates_to_http_client():
    class FakeHttpClient:
        def request(self, method, path, **kwargs):
            return {"method": method, "path": path, **kwargs}

    client = object.__new__(DouyinPayClient)
    client._http = FakeHttpClient()

    call = client.request(
        "POST",
        "/v1/trade/transactions/native",
        json={"mchid": "mch-1"},
        params={"appid": "app-1"},
        response_type="json",
    )

    assert call == {
        "method": "POST",
        "path": "/v1/trade/transactions/native",
        "json": {"mchid": "mch-1"},
        "params": {"appid": "app-1"},
        "body": None,
        "headers": None,
        "files": None,
        "response_type": "json",
    }


def test_service_request_uses_merchant_supplied_path_and_payload():
    service = Service(FakeClient())

    call = service.post(
        "/v1/payscore/serviceorder/{out_order_no}/sync",
        json={"mchid": "mch-1"},
        path_params={"out_order_no": "order/with space"},
        timeout=3,
    )

    assert call == {
        "method": "POST",
        "path": "/v1/payscore/serviceorder/order%2Fwith%20space/sync",
        "json": {"mchid": "mch-1"},
        "params": None,
        "timeout": 3,
    }


def test_service_get_uses_merchant_supplied_query():
    service = Service(FakeClient())

    call = service.get(
        "/v1/trade/transactions/out-trade-no/{out_trade_no}",
        params={"mchid": "mch-1"},
        path_params={"out_trade_no": "order-1"},
    )

    assert call == {
        "method": "GET",
        "path": "/v1/trade/transactions/out-trade-no/order-1",
        "json": None,
        "params": {"mchid": "mch-1"},
    }


def test_service_post_accepts_partner_supplied_path_and_payload():
    service = Service(FakeClient())

    call = service.post(
        "/v1/trade/partner/transactions/native",
        json={
            "sp_mchid": "sp-mch-1",
            "sp_appid": "sp-app-1",
            "sub_mchid": "sub-mch-1",
            "sub_appid": "sub-app-1",
            "out_trade_no": "order-1",
        },
    )

    assert call == {
        "method": "POST",
        "path": "/v1/trade/partner/transactions/native",
        "json": {
            "sp_mchid": "sp-mch-1",
            "sp_appid": "sp-app-1",
            "sub_mchid": "sub-mch-1",
            "sub_appid": "sub-app-1",
            "out_trade_no": "order-1",
        },
        "params": None,
    }


def test_service_path_escapes_template_params_for_any_api_path():
    service = Service(FakeClient())

    path_client = service.path(
        "/v1/trade/partner/transactions/out-trade-no/{out_trade_no}",
        out_trade_no="partner/order 1",
    )

    assert path_client.path == "/v1/trade/partner/transactions/out-trade-no/partner%2Forder%201"


def test_services_entry_is_thin_generic_service():
    services = DouyinPayServices(FakeClient())

    call = services.post("/v1/trade/refund/domestic/refunds", json={"out_refund_no": "refund-1"})

    assert call == {
        "method": "POST",
        "path": "/v1/trade/refund/domestic/refunds",
        "json": {"out_refund_no": "refund-1"},
        "params": None,
    }
    assert not hasattr(services, "native_pay")
    assert not hasattr(services, "refund")
    assert not hasattr(services, "payscore")
    assert not hasattr(services, "partnerpay")


def test_missing_path_param_raises_value_error():
    service = Service(FakeClient())

    with pytest.raises(ValueError):
        service.get("/v1/trade/transactions/out-trade-no/{out_trade_no}", path_params={"out_trade_no": ""})
