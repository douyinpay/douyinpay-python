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
| 通用 API 调用 | 通过 `sdk.request(...)` 或 `sdk.path("/v1/xxx").get/post/put/patch/delete` 调用接口，商户自行传入 path 和参数 |
| 薄 Service 入口 | `sdk.services` 仅提供通用 `request/get/post/put/patch/delete` 包装，不维护业务接口字段列表 |

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

resp = sdk.request("POST", "/v1/trade/transactions/native", json={
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
    resp = sdk.request("POST", "/v1/trade/transactions/native", json={...})
finally:
    if sdk.certificate_manager:
        sdk.certificate_manager.stop()
```

## 回调处理

HTTP 回调入口由业务自己的 Web 框架负责。SDK 不启动回调服务，只负责对抖音支付回调请求做验签、解密和解析：

```python
from bytedance import douyinpay

sdk = douyinpay.create_auto_rsa_client(
    mchid="80001234567",
    serial="MCH_SERIAL_NO",
    private_key="/path/to/merchant_private_key.pem",
    encrypt_key="YOUR_API_V3_KEY",
)

def handle_douyinpay_callback(headers, body):
    notify = sdk.parse_callback(headers, body)
    event_type = notify.event_type
    content = notify.content or {}

    if event_type and event_type.startswith("PAYMENT"):
        out_trade_no = content.get("out_trade_no")
        # 处理业务逻辑：幂等更新订单状态
        print(f"订单 {out_trade_no} 支付成功")

    return {"code": "SUCCESS", "message": "OK"}
```

> **安全红线**：回调必须**先验签**再解密，再处理业务；务必做幂等处理。

自动证书模式下，SDK 会复用 client 里的证书管理器获取最新平台证书，不需要业务额外维护 `PLATFORM_CERTS`。联调时可以临时把刷新间隔调短，确认会自动请求平台证书接口：

```python
sdk = douyinpay.create_auto_rsa_client(
    mchid="80001234567",
    serial="MCH_SERIAL_NO",
    private_key="/path/to/merchant_private_key.pem",
    encrypt_key="YOUR_API_V3_KEY",
    refresh_interval_sec=10,  # 仅用于联调验证；生产建议使用默认 24h
)
```

如果使用单证书模式，建议在初始化 client 时传入 `encrypt_key`，然后沿用同一个回调写法：

```python
sdk = douyinpay.create_rsa_client(
    mchid="80001234567",
    serial="MCH_SERIAL_NO",
    private_key="/path/to/merchant_private_key.pem",
    platform_certificate="/path/to/platform_cert.pem",
    encrypt_key="YOUR_API_V3_KEY",
)

notify = sdk.parse_callback(headers, body)
```

也可以继续使用独立函数处理回调，适合手动管理平台证书的场景：

```python
notify = douyinpay.parse_callback(
    headers=headers,
    body=body,
    encrypt_key="YOUR_API_V3_KEY",
    certs=PLATFORM_CERTS,
    sign_type=douyinpay.SignType.RSA,
)
```

## 通用 API 调用

SDK 不维护业务接口字段列表。商户根据接口文档自行传入 API 相对路径、请求体和查询参数；请求签名、验签、base URL 拼接仍由底层 `HttpClient` 统一处理：

```python
sdk.request("POST", "/v1/merchant/xxx", json=json_data)  # 通用直接调用
sdk.request("GET", "/v1/merchant/xxx", params={"mchid": "80001234567"})

# sdk.services 是同一套通用调用能力的薄封装
sdk.services.post("/v1/trade/transactions/native", json=json_data)
sdk.services.get("/v1/trade/transactions/out-trade-no/ORDER-001", params={"mchid": "80001234567"})

# 需要 path 参数转义时，可以使用 path_params
sdk.services.post(
    "/v1/payscore/serviceorder/{out_order_no}/sync",
    json=json_data,
    path_params={"out_order_no": "ORDER-001"},
)

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
