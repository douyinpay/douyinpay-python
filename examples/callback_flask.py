# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

import os

from flask import Flask, jsonify, request

from bytedance import douyinpay

MCHID = os.getenv("DOUYINPAY_MCHID", "")
MCH_SERIAL = os.getenv("DOUYINPAY_MCH_SERIAL", "")
MCH_PRIVATE_KEY_PATH = os.getenv("DOUYINPAY_MCH_PRIVATE_KEY_PATH", "")
API_V3_KEY = os.getenv("DOUYINPAY_API_V3_KEY", "")
PLATFORM_CERT_PATH = os.getenv("DOUYINPAY_PLATFORM_CERT_PATH", "")
REFRESH_INTERVAL_SEC = int(os.getenv("DOUYINPAY_CERT_REFRESH_INTERVAL_SEC", str(24 * 60 * 60)))


def create_app(douyinpay_client):
    """Create a Flask app with an already initialized DouyinPayClient."""
    app = Flask(__name__)

    @app.route("/callback/douyinpay", methods=["POST"])
    def callback():
        headers = dict(request.headers)
        raw_body = request.get_data(as_text=True)
        try:
            notify = douyinpay_client.parse_callback(headers, raw_body)
        except douyinpay.DouYinPaySignatureError as e:
            app.logger.warning(f"回调验签失败: {e}")
            return jsonify({"code": "FAIL", "message": "verify signature failed"}), 400
        except Exception as e:
            app.logger.error(f"回调处理异常: {e}")
            return jsonify({"code": "FAIL", "message": "internal error"}), 500
        event_type = notify.event_type
        content = notify.content or {}
        app.logger.info(f"收到回调 event={event_type} trade={content.get('out_trade_no')}")
        if event_type and event_type.startswith("PAYMENT"):
            out_trade_no = content.get("out_trade_no")
            amount = content.get("amount")
            app.logger.info(f"支付成功 订单={out_trade_no} 金额={amount}")
        elif event_type and event_type.startswith("REFUND"):
            app.logger.info(f"退款回调: {content}")
        return jsonify({"code": "SUCCESS", "message": "OK"})

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
    app = Flask(__name__)

    @app.route("/callback/douyinpay", methods=["POST"])
    def callback():
        return jsonify({"code": "FAIL", "message": "callback handler not initialized"}), 500


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=8080)
    finally:
        if sdk is not None:
            sdk.close()
