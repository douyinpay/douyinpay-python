import os
import douyinpay

MCHID = os.getenv("DOUYINPAY_MCHID", "")
APPID = os.getenv("DOUYINPAY_APPID", "")
MCH_SERIAL = os.getenv("DOUYINPAY_MCH_SERIAL", "")
MCH_PRIVATE_KEY_PATH = os.getenv("DOUYINPAY_MCH_PRIVATE_KEY_PATH", "")
API_V3_KEY = os.getenv("DOUYINPAY_API_V3_KEY", "")


def main():
    if not (MCHID and APPID and MCH_SERIAL and MCH_PRIVATE_KEY_PATH and API_V3_KEY):
        print("请设置环境变量: DOUYINPAY_MCHID, DOUYINPAY_APPID, DOUYINPAY_MCH_SERIAL, DOUYINPAY_MCH_PRIVATE_KEY_PATH, DOUYINPAY_API_V3_KEY")
        return

    sdk = douyinpay.create_auto_rsa_client(
        mchid=MCHID,
        serial=MCH_SERIAL,
        private_key=MCH_PRIVATE_KEY_PATH,
        encrypt_key=API_V3_KEY,
    )
    try:
        out_trade_no = f"autorsa-{int(__import__('time').time())}"
        req_data = {
            "mchid": MCHID,
            "appid": APPID,
            "description": "RSA自动证书Native支付",
            "out_trade_no": out_trade_no,
            "amount": {
                "currency": "CNY",
                "total": 1,
            },
            "ip": os.getenv("DOUYINPAY_CLIENT_IP", "127.0.0.1"),
            "notify_url": os.getenv("DOUYINPAY_NOTIFY_URL", "https://example.com/callback"),
        }
        resp = sdk.path("/v1/trade/transactions/native").post(req_data)
        print(f"自动证书RSA Native下单 status={resp.status_code}, data={resp.data}")
    finally:
        if sdk.certificate_manager:
            sdk.certificate_manager.stop()


if __name__ == "__main__":
    main()
