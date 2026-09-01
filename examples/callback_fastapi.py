# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from bytedance import douyinpay

MCHID = os.getenv("DOUYINPAY_MCHID", "")
MCH_SERIAL = os.getenv("DOUYINPAY_MCH_SERIAL", "")
MCH_PRIVATE_KEY_PATH = os.getenv("DOUYINPAY_MCH_PRIVATE_KEY_PATH", "")
API_V3_KEY = os.getenv("DOUYINPAY_API_V3_KEY", "")
PLATFORM_CERT_PATH = os.getenv("DOUYINPAY_PLATFORM_CERT_PATH", "")
REFRESH_INTERVAL_SEC = int(os.getenv("DOUYINPAY_CERT_REFRESH_INTERVAL_SEC", str(24 * 60 * 60)))


def create_app(douyinpay_client):
    """Create a FastAPI app with an already initialized DouyinPayClient."""
    app = FastAPI(title="抖音支付回调示例")

    @app.post("/callback/douyinpay")
    async def callback(request: Request):
        headers = dict(request.headers)
        raw_body = (await request.body()).decode("utf-8")
        try:
            notify = douyinpay_client.parse_callback(headers, raw_body)
        except douyinpay.DouYinPaySignatureError:
            return JSONResponse(status_code=400, content={"code": "FAIL", "message": "verify signature failed"})
        except Exception:
            return JSONResponse(status_code=500, content={"code": "FAIL", "message": "internal error"})
        event_type = notify.event_type
        content = notify.content or {}
        if event_type and event_type.startswith("PAYMENT"):
            print(f"[FastAPI] 支付成功: {content.get('out_trade_no')} 金额={content.get('amount')}")
        return {"code": "SUCCESS", "message": "OK"}

    return app


def _build_demo_client():
    """Build one client for running this example as a standalone demo."""
    if not (MCHID and MCH_SERIAL and MCH_PRIVATE_KEY_PATH and API_V3_KEY):
        return None
    if PLATFORM_CERT_PATH:
        return douyinpay.create_rsa_client(
            mchid=MCHID,
            serial=MCH_SERIAL,
            private_key=MCH_PRIVATE_KEY_PATH,
            platform_certificate=PLATFORM_CERT_PATH,
            encrypt_key=API_V3_KEY,
        )
    return douyinpay.create_auto_rsa_client(
        mchid=MCHID,
        serial=MCH_SERIAL,
        private_key=MCH_PRIVATE_KEY_PATH,
        encrypt_key=API_V3_KEY,
        refresh_interval_sec=REFRESH_INTERVAL_SEC,
    )


sdk = _build_demo_client()
if sdk is not None:
    app = create_app(sdk)
else:
    app = FastAPI(title="抖音支付回调示例")

    @app.post("/callback/douyinpay")
    async def callback(request: Request):
        raise HTTPException(status_code=500, detail="callback handler not initialized")
