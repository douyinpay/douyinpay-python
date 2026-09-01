# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bytedance.douyinpay.client import DouyinPayClient
from bytedance.douyinpay.services import (
    AppPayService,
    BillService,
    CertificateService,
    DouyinPayServices,
    NativePayService,
    PartnerAppPayService,
    PartnerBillService,
    PartnerPayScoreService,
    PayScoreService,
    RefundService,
)


class FakePathClient:
    def __init__(self, owner, path):
        self.owner = owner
        self.path = path

    def get(self, params=None, **kwargs):
        return self.owner.record("GET", self.path, params=params, **kwargs)

    def post(self, json=None, files=None, **kwargs):
        return self.owner.record("POST", self.path, json=json, files=files, **kwargs)

    def put(self, json=None, files=None, **kwargs):
        return self.owner.record("PUT", self.path, json=json, files=files, **kwargs)

    def patch(self, json=None, files=None, **kwargs):
        return self.owner.record("PATCH", self.path, json=json, files=files, **kwargs)

    def delete(self, **kwargs):
        return self.owner.record("DELETE", self.path, **kwargs)


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


def test_direct_pay_service_prepay_and_query():
    client = FakeClient()
    service = AppPayService(client)

    prepay = service.prepay({"mchid": "mch-1", "out_trade_no": "order-1"})
    query = service.query_order_by_out_trade_no("order-1", mchid="mch-1")

    assert prepay == {
        "method": "POST",
        "path": "/v1/trade/transactions/app",
        "json": {"mchid": "mch-1", "out_trade_no": "order-1"},
        "files": None,
    }
    assert query == {
        "method": "GET",
        "path": "/v1/trade/transactions/out-trade-no/order-1",
        "params": {"mchid": "mch-1"},
    }


def test_close_order_escapes_path_param_and_sends_mchid_body():
    client = FakeClient()
    service = NativePayService(client)

    call = service.close_order("order/with space", mchid="mch-1")

    assert call["method"] == "POST"
    assert call["path"] == "/v1/trade/transactions/out-trade-no/order%2Fwith%20space/close"
    assert call["json"] == {"mchid": "mch-1"}


def test_refund_query_merges_direct_and_partner_params():
    client = FakeClient()
    service = RefundService(client)

    call = service.query_by_out_refund_no(
        "refund-1",
        mchid="mch-1",
        sp_mchid="sp-1",
        params={"appid": "app-1"},
    )

    assert call == {
        "method": "GET",
        "path": "/v1/trade/refund/domestic/refunds/refund-1",
        "params": {"appid": "app-1", "mchid": "mch-1", "sp_mchid": "sp-1"},
    }


def test_partner_pay_service_uses_partner_paths_and_params():
    client = FakeClient()
    service = PartnerAppPayService(client)

    prepay = service.prepay({"sp_mchid": "sp-1", "sub_mchid": "sub-1"})
    query = service.query_order_by_id("tx-1", sp_mchid="sp-1", sub_mchid="sub-1")

    assert prepay["path"] == "/v1/trade/partner/transactions/app"
    assert query == {
        "method": "GET",
        "path": "/v1/trade/partner/transactions/id/tx-1",
        "params": {"sp_mchid": "sp-1", "sub_mchid": "sub-1"},
    }


def test_services_aggregator_exposes_common_services():
    client = FakeClient()
    services = DouyinPayServices(client)

    assert services.native_pay.prepay({"mchid": "mch-1"})["path"] == "/v1/trade/transactions/native"
    assert services.refund.create({"out_refund_no": "refund-1"})["path"] == "/v1/trade/refund/domestic/refunds"
    assert services.bill.apply_bill({"bill_date": "2026-08-31"})["path"] == "/v1/bill/billapply"
    assert services.partner_bill.apply_trade_bill({"bill_date": "2026-08-31"})["path"] == "/v1/bill/tradebill"
    assert services.payscore.post("/v1/payscore/custom", {"mchid": "mch-1"})["path"] == "/v1/payscore/custom"


def test_bill_service_boundaries_follow_go_services():
    direct = BillService(FakeClient())
    partner = PartnerBillService(FakeClient())

    assert not hasattr(direct, "apply_trade_bill")
    assert direct.apply_bill({"bill_date": "2026-08-31"})["path"] == "/v1/bill/billapply"
    assert partner.apply_trade_bill({"bill_date": "2026-08-31"})["path"] == "/v1/bill/tradebill"
    assert not hasattr(partner, "apply_bill")


def test_certificate_service_uses_core_certificate_path():
    call = CertificateService(FakeClient()).download_certificates()

    assert call["method"] == "GET"
    assert call["path"] == "/v1/merchant/certificates/getPlatformCertificates"


def test_client_services_property_builds_aggregator_once():
    client = object.__new__(DouyinPayClient)
    client._services = None

    services = client.services

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
        "/v1/payscore/custom",
        json={"mchid": "mch-1"},
        params={"appid": "app-1"},
        response_type="json",
    )

    assert call == {
        "method": "POST",
        "path": "/v1/payscore/custom",
        "json": {"mchid": "mch-1"},
        "params": {"appid": "app-1"},
        "body": None,
        "headers": None,
        "files": None,
        "response_type": "json",
    }


def test_payscore_service_uses_merchant_supplied_path_and_payload():
    client = FakeClient()
    service = PayScoreService(client)

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


def test_partner_payscore_service_uses_merchant_supplied_query():
    client = FakeClient()
    service = PartnerPayScoreService(client)

    call = service.get(
        "/v1/payscore/partner/serviceorder/query",
        params={"sp_mchid": "sp-1", "sub_mchid": "sub-1"},
    )

    assert call == {
        "method": "GET",
        "path": "/v1/payscore/partner/serviceorder/query",
        "json": None,
        "params": {"sp_mchid": "sp-1", "sub_mchid": "sub-1"},
    }


def test_missing_path_param_raises_value_error():
    client = FakeClient()
    service = NativePayService(client)

    with pytest.raises(ValueError):
        service.query_order_by_id("", mchid="mch-1")
