# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from bytedance import douyinpay

app = FastAPI(title="抖音支付回调示例")

API_V3_KEY = os.getenv("DOUYINPAY_API_V3_KEY", "")
PLATFORM_CERT_PATH = os.getenv("DOUYINPAY_PLATFORM_CERT_PATH", "")
SIGN_TYPE = os.getenv("DOUYINPAY_SIGN_TYPE", douyinpay.SignType.RSA)

_certs = {}
if PLATFORM_CERT_PATH:
    from bytedance.douyinpay.utils.pem import read_key_data, get_certificate_serial_number, add_certificate
    pem_bytes = read_key_data(PLATFORM_CERT_PATH)
    serial = get_certificate_serial_number(pem_bytes)
    add_certificate(_certs, pem_bytes, serial)


@app.post("/callback/douyinpay")
async def callback(request: Request):
    if not API_V3_KEY:
        raise HTTPException(status_code=500, detail="API_V3_KEY not set")
    headers = dict(request.headers)
    raw_body = (await request.body()).decode("utf-8")
    try:
        notify = douyinpay.parse_callback(
            headers=headers,
            body=raw_body,
            encrypt_key=API_V3_KEY,
            certs=_certs,
            sign_type=SIGN_TYPE,
        )
    except douyinpay.DouYinPaySignatureError:
        return JSONResponse(status_code=400, content={"code": "FAIL", "message": "verify signature failed"})
    except Exception:
        return JSONResponse(status_code=500, content={"code": "FAIL", "message": "internal error"})
    event_type = notify.event_type
    content = notify.content or {}
    if event_type and event_type.startswith("PAYMENT"):
        print(f"[FastAPI] 支付成功: {content.get('out_trade_no')} 金额={content.get('amount')}")
    return {"code": "SUCCESS", "message": "OK"}
