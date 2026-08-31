# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

import os
from bytedance import douyinpay

MCHID = os.getenv("DOUYINPAY_MCHID", "")
APPID = os.getenv("DOUYINPAY_APPID", "")
MCH_SERIAL = os.getenv("DOUYINPAY_MCH_SERIAL", "")
SM2_PRIVATE_KEY_PATH = os.getenv("DOUYINPAY_SM2_PRIVATE_KEY_PATH", "")
SM2_PLATFORM_CERT_PATH = os.getenv("DOUYINPAY_SM2_PLATFORM_CERT_PATH", "")


def main():
    if not (MCHID and APPID and MCH_SERIAL and SM2_PRIVATE_KEY_PATH and SM2_PLATFORM_CERT_PATH):
        print("请设置环境变量: DOUYINPAY_MCHID, DOUYINPAY_APPID, DOUYINPAY_MCH_SERIAL, DOUYINPAY_SM2_PRIVATE_KEY_PATH, DOUYINPAY_SM2_PLATFORM_CERT_PATH")
        print("说明：SM2 国密模式使用 SM2 签名 + SM4 对称解密（国密合规场景）")
        return

    sdk = douyinpay.create_sm2_client(
        mchid=MCHID,
        serial=MCH_SERIAL,
        private_key=SM2_PRIVATE_KEY_PATH,
        platform_certificate=SM2_PLATFORM_CERT_PATH,
    )

    out_trade_no = f"sm2-native-{int(__import__('time').time())}"
    req_data = {
        "mchid": MCHID,
        "appid": APPID,
        "description": "SM2国密Native支付",
        "out_trade_no": out_trade_no,
        "amount": {
            "currency": "CNY",
            "total": 1,
        },
        "ip": os.getenv("DOUYINPAY_CLIENT_IP", "127.0.0.1"),
        "notify_url": os.getenv("DOUYINPAY_NOTIFY_URL", "https://example.com/callback"),
    }

    resp = sdk.path("/v1/trade/transactions/native").post(req_data)
    print(f"SM2国密模式Native下单: status={resp.status_code}, data={resp.data}")
    print(f"当前sign_type: {sdk.config.sign_type}, encrypt_type: {sdk.config.encrypt_type}")


if __name__ == "__main__":
    main()
