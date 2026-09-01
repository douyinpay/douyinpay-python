# 抖音支付 Python 服务端 SDK (bytedance.douyinpay)

> 官方抖音支付服务端 Python SDK，支持 RSA 签名、AES-GCM 加密、单证书/自动证书两种初始化模式。

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)

## 安装

```bash
pip install bytedance.douyinpay
```

或在 `requirements.txt` 中固定：

```txt
bytedance.douyinpay>=1.0.0,<2.0.0
```

## 功能概览

| 能力 | 说明 |
|------|------|
| 请求签名 | RSA / SHA256withRSA / PKCS1v15 |
| 回调解密 | AES-256-GCM |
| 单证书模式 | 使用本地平台证书验签 |
| 自动证书模式 | SDK 自动下载并定时刷新平台证书 |
| Service API 调用 | 通过 `sdk.services.xxx` 调用已封装业务接口，覆盖支付、退款、账单、签约、代扣、收银台、证书等常用能力 |
| 通用 API 调用 | 通过 `sdk.request(...)` 或 `sdk.path("/v1/xxx").get/post/put/patch/delete` 访问未封装接口，以及 path/参数由商户自定义的接口 |

回调处理通过 `CallbackHandler` 先使用平台证书验签，再使用 APIv3 密钥解密资源内容。

## 初始化方式对比

| 模式 | 工厂函数 | 适用场景 | 是否需要传入平台证书 |
|------|---------|---------|------------------------|
| RSA 单证书 | `create_rsa_client()` | 平台证书手动管理 | 是 |
| RSA 自动证书 | `create_auto_rsa_client()` | 自动下载+每24h刷新（推荐）| 否，首次 bootstrap |

## 初始化参数说明

| 参数 | 单证书模式 | 自动证书模式 | 说明 |
|------|------------|--------------|------|
| `mchid` | 必填 | 必填 | 商户号 |
| `serial` | 必填 | 必填 | 商户 API 证书序列号，会写入请求 `Authorization.serial_no` |
| `private_key` | 必填 | 必填 | 商户 API 私钥，用于请求签名 |
| `platform_certificate` | 必填 | 不需要 | 抖音支付平台证书 PEM，用于响应和回调验签 |
| `encrypt_key` | 可选；需要 `sdk.parse_callback()` 时建议传入，也可调用 `parse_callback()` 时单独传 | 必填 | APIv3 密钥，用于解密平台证书和回调资源 |

单证书模式传入完整平台证书 PEM 时，SDK 会自动解析平台证书序列号，不需要额外传平台证书序列号。
自动证书模式会自动下载并缓存平台证书，因此初始化时不需要传 `platform_certificate`。

## 快速开始

### RSA 单证书模式

```python
from bytedance import douyinpay

sdk = douyinpay.create_rsa_client(
    mchid="80001234567",
    serial="MCH_SERIAL_NO",
    private_key="/path/to/merchant_private_key.pem",
    platform_certificate="/path/to/platform_cert.pem",
    encrypt_key="YOUR_API_V3_KEY",  # 需要用 sdk.parse_callback() 时传入
)

resp = sdk.services.native_pay.prepay({
    "mchid": "80001234567",
    "appid": "your_appid",
    "description": "Native支付示例",
    "out_trade_no": "ORDER-001",
    "amount": {
        "currency": "CNY",
        "total": 1,
    },
    "ip": "127.0.0.1",
    "notify_url": "https://your-host/callback/douyinpay",
})

print(resp.status_code, resp.data)
```

### RSA 自动证书模式（推荐）

```python
from bytedance import douyinpay

sdk = douyinpay.create_auto_rsa_client(
    mchid="80001234567",
    serial="MCH_SERIAL_NO",
    private_key="/path/to/merchant_private_key.pem",
    encrypt_key="YOUR_API_V3_KEY",  # 32字节 APIv3 密钥
)
try:
    resp = sdk.services.native_pay.prepay({...})
finally:
    if sdk.certificate_manager:
        sdk.certificate_manager.stop()
```

## 回调处理（Flask 示例）

```python
from flask import Flask, request, jsonify
from bytedance import douyinpay

app = Flask(__name__)

API_V3_KEY = "YOUR_API_V3_KEY"
PLATFORM_CERTS = {}  # 加载方式见 examples/callback_flask.py

@app.post("/callback/douyinpay")
def callback():
    headers = dict(request.headers)
    body = request.get_data(as_text=True)
    notify = douyinpay.parse_callback(
        headers=headers, body=body,
        encrypt_key=API_V3_KEY,
        certs=PLATFORM_CERTS,
        sign_type=douyinpay.SignType.RSA,
    )
    event_type = notify.event_type
    content = notify.content or {}
    if event_type and event_type.startswith("PAYMENT"):
        out_trade_no = content.get("out_trade_no")
        # 处理业务逻辑：幂等更新订单状态
        print(f"订单 {out_trade_no} 支付成功")
    return {"code": "SUCCESS", "message": "OK"}
```

> **安全红线**：回调必须**先验签**再解密，再处理业务；务必做幂等处理。

如果使用自动证书模式，或在单证书模式初始化时传入了 `encrypt_key`，也可以直接复用 client 配置处理回调：

```python
notify = sdk.parse_callback(headers, body)
```

## Service 调用

SDK 推荐对稳定接口使用 service 层调用。service 只固定 API path、HTTP method、path/query 参数；请求签名、验签、base URL 拼接仍由底层 `HttpClient` 统一处理。对于 path 或参数由商户自定义的接口，使用通用 API 调用入口。

| Service | 常用方法 |
|---------|----------|
| `app_pay` / `h5_pay` / `jsapi_pay` / `native_pay` | `prepay(req)`、`close_order(out_trade_no, ...)`、`query_order_by_id(transaction_id, ...)`、`query_order_by_out_trade_no(out_trade_no, ...)` |
| `contract_order_pay` / `credit_contract_order_pay` | `prepay(req)`、`close_order(...)`、`query_order_by_id(...)`、`query_order_by_out_trade_no(...)` |
| `partner_app_pay` / `partner_h5_pay` / `partner_jsapi_pay` / `partner_native_pay` | 服务商下单、关单、按交易单号/商户订单号查询 |
| `partner_contract_pay` | `contract_order(req)`、`pay_apply(req)` |
| `refund` | `create(req)`、`query_by_out_refund_no(out_refund_no, ...)` |
| `bill` | `apply_bill(params)`、`apply_fund_flow_bill(params)`、`apply_split_bill(params)` |
| `partner_bill` | `apply_trade_bill(params)`、`apply_fund_flow_bill(params)`、`apply_split_bill(params)` |
| `contract` | `query_contract(req)`、`delete_contract(req)`、`pre_entrust_web(req)`、`h5_entrust_web(req)` |
| `partner_contract` | `query_contract(plan_id, out_contract_code, ...)`、`terminate_contract(plan_id, out_contract_code, req)` |
| `deduct` | `deduct(req)`、`pay_apply(req)`、`deduct_notify(req)` |
| `partner_deduct` | `contract_schedule(contract_id, req)`、`contract_schedule_query(contract_id, ...)` |
| `payscore` / `partner_payscore` | 通用支付分 API 调用入口，商户自行传入 path、params、json |
| `cashier` | `prepay_consult(req)` |
| `certificate` | `download_certificates()` |

```python
sdk.services.native_pay.prepay(json_data)
sdk.services.native_pay.query_order_by_out_trade_no("ORDER-001", mchid="80001234567")
sdk.services.refund.create(refund_data)
```

支付分等 path/参数不固定的接口使用通用入口：

```python
sdk.services.payscore.post("/v1/payscore/serviceorder/create", json=req)
sdk.services.payscore.get("/v1/payscore/serviceorder/query", params=query)
sdk.services.partner_payscore.post("/v1/payscore/partner/serviceorder/create", json=req)
```

## 通用 API 调用

对于 SDK 暂未封装、或 path/参数不适合固化在 SDK 内的接口，可以使用通用调用入口。`path` 只传 API 相对路径，`base_url` / `base_uri` 由 client 配置统一管理：

```python
sdk.request("POST", "/v1/merchant/xxx", json=json_data)  # 通用直接调用
sdk.request("GET", "/v1/merchant/xxx", params={"mchid": "80001234567"})
sdk.path("/v1/merchant/xxx").get(params={"mchid": "80001234567"})  # GET + Query
sdk.path("/v1/merchant/xxx").put(json_data)  # PUT
sdk.path("/v1/resource/xxx").patch(json_data)  # PATCH（已支持）
sdk.path("/v1/resource/xxx").delete()         # DELETE
```

## 错误处理

| 异常类 | 场景 |
|--------|------|
| `DouYinPayInvalidArgumentError` | 初始化参数校验失败（mchid 空、密钥加载失败等）|
| `DouYinPaySignatureError` | 签名、验签失败（时间偏移、serial 不匹配、签名不通过）|
| `DouYinPayAPIError` | HTTP 状态码 ≥400，含 `status_code` / `response_body` 字段 |
| `DouYinPayCertificateError` | 证书下载 / 解密失败 |
| `DouYinPayError` | 其他通用异常（回调解密算法不支持等） |

## 安全建议

1. **私钥与 APIv3 密钥严禁硬编码**，使用环境变量、密钥管理服务或文件权限 600 管理。
2. 密钥加载支持**文件路径**，避免把密钥内容放入内存变量：
   ```python
   private_key="/etc/douyinpay/mch_private.pem"  # ✅ 推荐
   ```
3. 金额统一使用**整数（分）**，严禁使用浮点数。
4. 日志与异常中严禁打印 `Authorization` 头完整内容；`on_request` 回调请自行脱敏。
5. 回调验签通过后再解密；**回调验签失败直接返回 4xx，不执行业务**。

## 依赖

- Python >= 3.8
- `httpx>=0.25.0`：现代同步+异步 HTTP 客户端
- `cryptography>=41.0.0`：RSA + AES（安全审计）

## License

Apache-2.0 © 抖音支付
