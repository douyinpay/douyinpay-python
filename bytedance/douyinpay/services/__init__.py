# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

from .base import Service
from .bill import BillService, PartnerBillService
from .cashier import CashierService
from .certificates import CertificateService
from .contract import ContractService
from .deduct import DeductService, PartnerDeductService
from .partnercontract import PartnerContractService
from .partnerpay import (
    PartnerAppPayService,
    PartnerContractPayService,
    PartnerH5PayService,
    PartnerJsapiPayService,
    PartnerNativePayService,
    PartnerTransactionService,
)
from .pay import (
    AppPayService,
    ContractOrderPayService,
    CreditContractOrderPayService,
    H5PayService,
    JsapiPayService,
    NativePayService,
    TransactionService,
)
from .payscore import PartnerPayScoreService, PayScoreService
from .refund import RefundService


class DouyinPayServices:
    def __init__(self, client):
        self.client = client
        self.app_pay = AppPayService(client)
        self.h5_pay = H5PayService(client)
        self.jsapi_pay = JsapiPayService(client)
        self.native_pay = NativePayService(client)
        self.contract_order_pay = ContractOrderPayService(client)
        self.credit_contract_order_pay = CreditContractOrderPayService(client)
        self.partner_app_pay = PartnerAppPayService(client)
        self.partner_h5_pay = PartnerH5PayService(client)
        self.partner_jsapi_pay = PartnerJsapiPayService(client)
        self.partner_native_pay = PartnerNativePayService(client)
        self.partner_contract_pay = PartnerContractPayService(client)
        self.refund = RefundService(client)
        self.bill = BillService(client)
        self.partner_bill = PartnerBillService(client)
        self.contract = ContractService(client)
        self.partner_contract = PartnerContractService(client)
        self.deduct = DeductService(client)
        self.partner_deduct = PartnerDeductService(client)
        self.payscore = PayScoreService(client)
        self.partner_payscore = PartnerPayScoreService(client)
        self.cashier = CashierService(client)
        self.certificate = CertificateService(client)


__all__ = [
    "Service",
    "DouyinPayServices",
    "AppPayService",
    "H5PayService",
    "JsapiPayService",
    "NativePayService",
    "ContractOrderPayService",
    "CreditContractOrderPayService",
    "TransactionService",
    "PartnerAppPayService",
    "PartnerH5PayService",
    "PartnerJsapiPayService",
    "PartnerNativePayService",
    "PartnerTransactionService",
    "PartnerContractPayService",
    "RefundService",
    "BillService",
    "PartnerBillService",
    "ContractService",
    "PartnerContractService",
    "DeductService",
    "PartnerDeductService",
    "PayScoreService",
    "PartnerPayScoreService",
    "CashierService",
    "CertificateService",
]
