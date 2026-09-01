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
        print("请设置环境变量")
        return
    sdk = douyinpay.create_rsa_client(
        mchid=MCHID, serial=MCH_SERIAL,
        private_key=MCH_PRIVATE_KEY_PATH,
        platform_certificate=PLATFORM_CERT_PATH,
    )
    client_ip = os.getenv("DOUYINPAY_CLIENT_IP", "127.0.0.1")
    req = {
        "mchid": MCHID,
        "appid": APPID,
        "description": "H5支付测试商品",
        "out_trade_no": f"h5-{int(__import__('time').time())}",
        "amount": {
            "currency": "CNY",
            "total": 1,
        },
        "ip": client_ip,
        "notify_url": os.getenv("DOUYINPAY_NOTIFY_URL", "https://example.com/callback"),
        "scene_info": {
            "payer_client_ip": client_ip,
            "h5_info": {"type": "Wap"},
        },
    }
    resp = sdk.request("POST", "/v1/trade/transactions/h5", json=req)
    print(f"H5支付下单: status={resp.status_code}, data={resp.data}")


if __name__ == "__main__":
    main()
