# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from bytedance import douyinpay

app = FastAPI(title="抖音支付回调示例")

MCHID = os.getenv("DOUYINPAY_MCHID", "")
MCH_SERIAL = os.getenv("DOUYINPAY_MCH_SERIAL", "")
MCH_PRIVATE_KEY_PATH = os.getenv("DOUYINPAY_MCH_PRIVATE_KEY_PATH", "")
API_V3_KEY = os.getenv("DOUYINPAY_API_V3_KEY", "")
PLATFORM_CERT_PATH = os.getenv("DOUYINPAY_PLATFORM_CERT_PATH", "")
SIGN_TYPE = os.getenv("DOUYINPAY_SIGN_TYPE", douyinpay.SignType.RSA)
REFRESH_INTERVAL_SEC = int(os.getenv("DOUYINPAY_CERT_REFRESH_INTERVAL_SEC", str(24 * 60 * 60)))


def _build_auto_client():
    if not (MCHID and MCH_SERIAL and MCH_PRIVATE_KEY_PATH and API_V3_KEY):
        return None
    return douyinpay.create_auto_rsa_client(
        mchid=MCHID,
        serial=MCH_SERIAL,
        private_key=MCH_PRIVATE_KEY_PATH,
        encrypt_key=API_V3_KEY,
        refresh_interval_sec=REFRESH_INTERVAL_SEC,
    )


def _build_manual_handler():
    if not (API_V3_KEY and PLATFORM_CERT_PATH):
        return None
    certs = {}
    from bytedance.douyinpay.utils.pem import add_certificate, get_certificate_serial_number, read_key_data

    pem_bytes = read_key_data(PLATFORM_CERT_PATH)
    serial = get_certificate_serial_number(pem_bytes)
    add_certificate(certs, pem_bytes, serial)
    return douyinpay.CallbackHandler(
        encrypt_key=API_V3_KEY,
        certs=certs,
        sign_type=SIGN_TYPE,
    )


sdk = _build_auto_client()
manual_handler = None if sdk else _build_manual_handler()


@app.post("/callback/douyinpay")
async def callback(request: Request):
    if sdk is None and manual_handler is None:
        raise HTTPException(status_code=500, detail="callback handler not initialized")
    headers = dict(request.headers)
    raw_body = (await request.body()).decode("utf-8")
    try:
        notify = sdk.parse_callback(headers, raw_body) if sdk else manual_handler.parse(headers, raw_body)
    except douyinpay.DouYinPaySignatureError:
        return JSONResponse(status_code=400, content={"code": "FAIL", "message": "verify signature failed"})
    except Exception:
        return JSONResponse(status_code=500, content={"code": "FAIL", "message": "internal error"})
    event_type = notify.event_type
    content = notify.content or {}
    if event_type and event_type.startswith("PAYMENT"):
        print(f"[FastAPI] 支付成功: {content.get('out_trade_no')} 金额={content.get('amount')}")
    return {"code": "SUCCESS", "message": "OK"}
