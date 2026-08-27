# Changelog

All notable changes to `douyinpay-python` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-08-26

### Added

- **四种初始化模式**：RSA 单证书、RSA 自动证书、SM2 单证书、SM2 自动证书（对齐 Go / Java SDK 完整功能矩阵）。
- **双签名算法**：RSA（SHA256withRSA/PKCS1v15）+ SM2（SM2withSM3，国密），通过统一 `SignerBase` 抽象分发。
- **双加密算法**：AES-256-GCM（RSA 模式）+ SM4-CBC + PKCS5Padding（SM2 模式），通过统一 `EncryptorBase` 抽象分发。
- **证书下载**：`download_platform_certificates()` 支持 bootstrap 模式（首次不验签）与刷新模式；根据 `encrypt_type` 自动选择 AES / SM4 解密。
- **证书自动管理**：`AutoCertificateManager` — 线程安全 `threading.Lock`、并发刷新 Event 去重、`daemon=True` 定时器（默认 24h）、双 serial 注册（API 返回 serial + PEM 解析 serial 同时注册）。
- **HTTP 客户端**：`HttpClient` 覆盖 `GET / POST / PUT / PATCH / DELETE`，支持：
  - `Douyinpay-Sdk-Agent` 四种统计头（RSA / AutoRSA / SM2 / AutoSM2，格式 `{Type}-PYTHON-v{ver}-{mchid}`）
  - `User-Agent: douyinpay-python/{version} httpx`
  - `base_uri` / `base_url` 别名兼容（PHP / Node.js 命名）
  - `on_request` 调试回调
  - HTTP 头大小写不敏感取响应头值
  - `skip_verify` 模式（证书 bootstrap 专用）
- **通用链式调用**：`sdk.path("/v1/xxx").post(data)` 通用接口，API 新增时无需升级 SDK。
- **回调处理**：`CallbackHandler` / `parse_callback()` 先验签、再按 `resource.algorithm` 字段动态选择 AES-GCM / SM4-CBC 解密；验签失败直接抛 `DouYinPaySignatureError`，保证顺序正确。
- **异常体系**：`DouYinPayError`（base）→ `InvalidArgumentError` / `SignatureError` / `APIError(status_code,response_body)` / `CertificateError`。
- **完整单元测试**：13 个测试文件覆盖 version / formatter / utils.http / utils.pem / crypto.rsa / crypto.aes / crypto.sm2 / crypto.sm4 / signer / http_client / callback / certificates / factory。
- **示例代码**：`examples/` 包含 Native(RSA/AutoRSA)、App、JSAPI、H5、退款、查单、Flask 回调、FastAPI 回调、SM2 国密 Native 共 10 个完整示例，全部使用环境变量不硬编码敏感信息。
- **项目工程化**：`pyproject.toml`（PEP 621）、`LICENSE`（Apache-2.0）、`.gitignore`、`pytest` + `pytest-httpx` + `pytest-cov` 配置、`ruff` + `mypy` 开发依赖。
