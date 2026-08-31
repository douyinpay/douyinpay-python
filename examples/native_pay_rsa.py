# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

import os
from bytedance import douyinpay

MCHID = os.getenv("DOUYINPAY_MCHID", "")
APPID = os.getenv("DOUYINPAY_APPID", "")
MCH_SERIAL = os.getenv("DOUYINPAY_MCH_SERIAL", "")
MCH_PRIVATE_KEY_PATH = os.getenv("DOUYINPAY_MCH_PRIVATE_KEY_PATH", "")
PLATFORM_CERT_PATH = os.getenv("DOUYINPAY_PLATFORM_CERT_PATH", "")


def main():
    if not (MCHID and APPID and MCH_SERIAL and MCH_PRIVATE_KEY_PATH and PLATFORM_CERT_PATH):
        print("请设置环境变量: DOUYINPAY_MCHID, DOUYINPAY_APPID, DOUYINPAY_MCH_SERIAL, DOUYINPAY_MCH_PRIVATE_KEY_PATH, DOUYINPAY_PLATFORM_CERT_PATH")
        return

    sdk = douyinpay.create_rsa_client(
        mchid=MCHID,
        serial=MCH_SERIAL,
        private_key=MCH_PRIVATE_KEY_PATH,
        platform_certificate=PLATFORM_CERT_PATH,
    )

    out_trade_no = f"native-{int(__import__('time').time())}"
    req_data = {
        "mchid": MCHID,
        "appid": APPID,
        "description": "Native支付测试商品",
        "out_trade_no": out_trade_no,
        "amount": {
            "currency": "CNY",
            "total": 1,
        },
        "ip": os.getenv("DOUYINPAY_CLIENT_IP", "127.0.0.1"),
        "notify_url": os.getenv("DOUYINPAY_NOTIFY_URL", "https://example.com/callback"),
    }

    resp = sdk.services.native_pay.prepay(req_data)
    print("Native支付下单成功:")
    print(f"  status_code: {resp.status_code}")
    print(f"  data: {resp.data}")


if __name__ == "__main__":
    main()
