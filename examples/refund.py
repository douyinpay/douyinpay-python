import os
import douyinpay

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
    req = {
        "mchid": MCHID,
        "appid": APPID,
        "out_trade_no": "ORDER-TO-REFUND",
        "out_refund_no": f"refund-{int(__import__('time').time())}",
        "reason": "用户申请退款",
        "amount": {
            "refund": 1,
            "total": 1,
            "currency": "CNY",
        },
        "notify_url": os.getenv("DOUYINPAY_REFUND_NOTIFY_URL", "https://example.com/refund-callback"),
    }
    resp = sdk.path("/v1/trade/refund/domestic/refunds").post(req)
    print(f"退款申请: status={resp.status_code}, data={resp.data}")


if __name__ == "__main__":
    main()
