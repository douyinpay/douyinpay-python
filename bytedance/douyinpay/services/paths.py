# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

APP_PREPAY = "/v1/trade/transactions/app"
H5_PREPAY = "/v1/trade/transactions/h5"
JSAPI_PREPAY = "/v1/trade/transactions/jsapi"
NATIVE_PREPAY = "/v1/trade/transactions/native"
CONTRACT_ORDER_PREPAY = "/v1/trade/transactions/contractorder"
CREDIT_CONTRACT_ORDER_PREPAY = "/v1/trade/transactions/payscorecontractorder"
CLOSE_ORDER = "/v1/trade/transactions/out-trade-no/{out_trade_no}/close"
QUERY_ORDER_BY_ID = "/v1/trade/transactions/id/{transaction_id}"
QUERY_ORDER_BY_OUT_TRADE_NO = "/v1/trade/transactions/out-trade-no/{out_trade_no}"

PARTNER_APP_PREPAY = "/v1/trade/partner/transactions/app"
PARTNER_H5_PREPAY = "/v1/trade/partner/transactions/h5"
PARTNER_JSAPI_PREPAY = "/v1/trade/partner/transactions/jsapi"
PARTNER_NATIVE_PREPAY = "/v1/trade/partner/transactions/native"
PARTNER_CONTRACT_ORDER = "/v1/trade/partner/transactions/contractorder"
PARTNER_PAY_APPLY = "/v1/trade/partner/deduct/payapply"
PARTNER_CLOSE_ORDER = "/v1/trade/partner/transactions/out-trade-no/{out_trade_no}/close"
PARTNER_QUERY_ORDER_BY_ID = "/v1/trade/partner/transactions/id/{transaction_id}"
PARTNER_QUERY_ORDER_BY_OUT_TRADE_NO = "/v1/trade/partner/transactions/out-trade-no/{out_trade_no}"

REFUND = "/v1/trade/refund/domestic/refunds"
REFUND_QUERY_BY_OUT_REFUND_NO = "/v1/trade/refund/domestic/refunds/{out_refund_no}"

BILL_APPLY = "/v1/bill/billapply"
TRADE_BILL = "/v1/bill/tradebill"
FUND_FLOW_BILL = "/v1/bill/fundflowbill"
SPLIT_BILL = "/v1/bill/splitbill"

QUERY_CONTRACT = "/v1/member/querycontract"
DELETE_CONTRACT = "/v1/member/deletecontract"
PRE_ENTRUST_WEB = "/v1/agreementauth/preentrustweb"
H5_ENTRUST_WEB = "/v1/agreementauth/h5entrustweb"

DEDUCT = "/v1/deduct/payapply"
DEDUCT_NOTIFY = "/v1/agreementauth/deductNotify"

PARTNER_QUERY_CONTRACT = (
    "/v1/agreementauth/partner/contracts/plan-id/{plan_id}/out-contract-code/{out_contract_code}"
)
PARTNER_TERMINATE_CONTRACT = (
    "/v1/agreementauth/partner/contracts/plan-id/{plan_id}/out-contract-code/{out_contract_code}/terminate"
)
PARTNER_CONTRACT_SCHEDULE = "/v1/agreementauth/partner/schedules/contract-id/{contract_id}/schedule"
PARTNER_CONTRACT_SCHEDULE_QUERY = "/v1/agreementauth/partner/schedules/contract-id/{contract_id}"

PREPAY_CONSULT = "/v1/cashier/prepay/consult"
