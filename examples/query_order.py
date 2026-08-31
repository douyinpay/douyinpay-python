# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

import os
from bytedance import douyinpay

MCHID = os.getenv("DOUYINPAY_MCHID", "")
MCH_SERIAL = os.getenv("DOUYINPAY_MCH_SERIAL", "")
MCH_PRIVATE_KEY_PATH = os.getenv("DOUYINPAY_MCH_PRIVATE_KEY_PATH", "")
PLATFORM_CERT_PATH = os.getenv("DOUYINPAY_PLATFORM_CERT_PATH", "")


def main():
    if not (MCHID and MCH_SERIAL and MCH_PRIVATE_KEY_PATH and PLATFORM_CERT_PATH):
        print("请设置环境变量")
        return
    sdk = douyinpay.create_rsa_client(
        mchid=MCHID, serial=MCH_SERIAL,
        private_key=MCH_PRIVATE_KEY_PATH,
        platform_certificate=PLATFORM_CERT_PATH,
    )
    out_trade_no = os.getenv("DOUYINPAY_QUERY_ORDER_NO", "SAMPLE-ORDER")
    resp = sdk.services.native_pay.query_order_by_out_trade_no(out_trade_no, mchid=MCHID)
    print(f"查单: status={resp.status_code}, data={resp.data}")


if __name__ == "__main__":
    main()
