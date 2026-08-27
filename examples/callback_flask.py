import os
import json
from flask import Flask, request, jsonify
import douyinpay

app = Flask(__name__)

API_V3_KEY = os.getenv("DOUYINPAY_API_V3_KEY", "")
PLATFORM_CERT_PATH = os.getenv("DOUYINPAY_PLATFORM_CERT_PATH", "")
SIGN_TYPE = os.getenv("DOUYINPAY_SIGN_TYPE", douyinpay.SignType.RSA)

_certs = {}
if PLATFORM_CERT_PATH:
    from douyinpay.utils.pem import read_key_data, get_certificate_serial_number, add_certificate
    pem_bytes = read_key_data(PLATFORM_CERT_PATH)
    serial = get_certificate_serial_number(pem_bytes)
    add_certificate(_certs, pem_bytes, serial)


@app.route("/callback/douyinpay", methods=["POST"])
def callback():
    if not API_V3_KEY:
        return jsonify({"code": "FAIL", "message": "API_V3_KEY not set"}), 500
    headers = dict(request.headers)
    raw_body = request.get_data(as_text=True)
    try:
        notify = douyinpay.parse_callback(
            headers=headers,
            body=raw_body,
            encrypt_key=API_V3_KEY,
            certs=_certs,
            sign_type=SIGN_TYPE,
        )
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
