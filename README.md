# 抖音支付 Python 服务端 SDK (byted-douyinpay-python)

> 官方抖音支付服务端 Python SDK，支持 **RSA + SM2 双签名算法**、**AES-GCM + SM4-CBC 双加密算法**、单证书/自动证书四种初始化模式。

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)

## 安装

```bash
pip install byted-douyinpay-python
```

或在 `requirements.txt` 中固定：

```txt
byted-douyinpay-python>=1.0.0,<2.0.0
```

## 功能概览

| 算法组合 | 签名算法 | 对称加密 | 单证书模式 | 自动证书模式 | Sdk-Agent 统计头 |
|---------|---------|---------|-----------|-------------|-----------------|
| RSA（通用） | SHA256withRSA / PKCS1v15 | AES-256-GCM | `create_rsa_client` | `create_auto_rsa_client` | `RSA-` / `AutoRSA-` |
| SM2（国密合规）| SM2withSM3 | SM4-CBC + PKCS5Padding | `create_sm2_client` | `create_auto_sm2_client` | `SM2-` / `AutoSM2-` |

回调处理通过 `CallbackHandler` 自动根据 `resource.algorithm` 字段动态选择 AES 或 SM4 解密器。

## 四种初始化方式对比

| 模式 | 工厂函数 | 适用场景 | 是否需要提前上传平台证书 |
|------|---------|---------|------------------------|
| RSA 单证书 | `create_rsa_client()` | 平台证书手动管理 | 是 |
| RSA 自动证书 | `create_auto_rsa_client()` | 自动下载+每24h刷新（推荐）| 否，首次 bootstrap |
| SM2 单证书 | `create_sm2_client()` | 国密合规渠道，手动管理 | 是 |
| SM2 自动证书 | `create_auto_sm2_client()` | 国密合规渠道+自动刷新 | 否，首次 bootstrap |

## 快速开始

### RSA 单证书模式

```python
import douyinpay

sdk = douyinpay.create_rsa_client(
    mchid="80001234567",
    serial="MCH_SERIAL_NO",
    private_key="/path/to/merchant_private_key.pem",
    platform_certificate="/path/to/platform_cert.pem",
)

resp = sdk.path("/v1/trade/transactions/native").post({
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
import douyinpay

sdk = douyinpay.create_auto_rsa_client(
    mchid="80001234567",
    serial="MCH_SERIAL_NO",
    private_key="/path/to/merchant_private_key.pem",
    encrypt_key="YOUR_API_V3_KEY",  # 32字节 APIv3 密钥
)
try:
    resp = sdk.path("/v1/trade/transactions/native").post({...})
finally:
    if sdk.certificate_manager:
        sdk.certificate_manager.stop()
```

### SM2 国密模式

```python
import douyinpay

sdk = douyinpay.create_sm2_client(
    mchid="80001234567",
    serial="MCH_SM2_SERIAL",
    private_key="/path/to/sm2_merchant_key.pem",
    platform_certificate="/path/to/sm2_platform_cert.pem",
)
# 后续调用同 RSA
```

## 回调处理（Flask 示例）

```python
from flask import Flask, request, jsonify
import douyinpay

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
        sign_type=douyinpay.SignType.RSA,  # SM2 商户此处传 SignType.SM2
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

## 通用链式调用

SDK 采用通用 path 调用，任意新增 API 无需升级 SDK：

```python
sdk.get_client("/v1/trade/transactions/native").post(json_data)  # POST
sdk.path("/v1/trade/transactions/out-trade-no/ORDER-001").get(params={"mchid": "80001234567"})  # GET + Query
sdk.path("/v1/merchant/xxx").put(json_data)  # PUT
sdk.path("/v1/resource/xxx").patch(json_data)  # PATCH（已支持）
sdk.path("/v1/resource/xxx").delete()         # DELETE
```

## SDK 统计头说明

每个请求自动携带两个 Header：

| Header | 格式示例 | 用途 |
|--------|---------|------|
| `User-Agent` | `douyinpay-python/1.0.0 httpx` | 版本统计与问题定位 |
| `Douyinpay-Sdk-Agent` | `RSA-PYTHON-v1.0.0-80001234567` | 按初始化模式（RSA/AutoRSA/SM2/AutoSM2）统计语言使用情况 |

跨 SDK 统一格式：`{AgentType}-{LANG}-v{version}-{mchid}`，已与 Go/Java/Node.js SDK 对齐。

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

## SM2 国密模式使用说明

- **使用场景**：国内金融支付合规要求、特定银行/渠道要求国密。
- **密钥格式**：SM2 私钥可使用标准 PEM（PKCS8 EC 格式），`gmssl>=3.2.2` 能正确解析。
- **算法绑定**：SM2 模式下对称加密自动使用 `SM4-CBC + PKCS5Padding`，与 Go/Java SDK 一致。
- **回调解密**：无需手动指定 `encrypt_type`，`CallbackHandler` 依据 `resource.algorithm` 字段自动选择。

## 依赖

- Python >= 3.8
- `httpx>=0.25.0`：现代同步+异步 HTTP 客户端
- `cryptography>=41.0.0`：RSA + AES（安全审计）
- `gmssl>=3.2.2`：纯 Python 国密算法（SM2/SM3/SM4）

## License

Apache-2.0 © 抖音支付
