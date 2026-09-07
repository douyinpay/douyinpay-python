# Changelog

All notable changes to `douyinpay-python` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.1] - 2026-09-07

### Changed

- Add PyPI project links for Homepage, Repository, and Issues.

### Fixed

- Close the temporary HTTP client used during platform certificate download.

## [1.0.0] - 2026-08-26

### Added

- **两种初始化模式**：RSA 单证书、RSA 自动证书。
- **签名算法**：RSA（SHA256withRSA/PKCS1v15）。
- **加密算法**：AES-256-GCM。
- **证书下载**：`download_platform_certificates()` 支持 bootstrap 模式（首次不验签）与刷新模式，并使用 AES 解密平台证书。
- **证书自动管理**：`AutoCertificateManager` — 线程安全 `threading.Lock`、并发刷新 Event 去重、`daemon=True` 定时器（默认 24h）、双 serial 注册（API 返回 serial + PEM 解析 serial 同时注册）。
- **Service API 调用**：`sdk.services` 仅提供通用 `request/get/post/put/patch/delete` 薄封装，不维护业务接口字段列表；通用 `sdk.path()` 继续作为同等能力入口。
- **HTTP 客户端**：`HttpClient` 覆盖 `GET / POST / PUT / PATCH / DELETE`，支持：
  - `User-Agent: douyinpay-python/{version} httpx`
  - `base_uri` / `base_url` 别名兼容（PHP / Node.js 命名）
  - `on_request` 调试回调
  - HTTP 头大小写不敏感取响应头值
  - `skip_verify` 模式（证书 bootstrap 专用）
- **通用链式调用**：`sdk.path("/v1/xxx").post(data)` 通用接口，API 新增时无需升级 SDK。
- **回调处理**：`CallbackHandler` / `parse_callback()` 先验签、再使用 AES-GCM 解密；验签失败直接抛 `DouYinPaySignatureError`，保证顺序正确。
- **异常体系**：`DouYinPayError`（base）→ `InvalidArgumentError` / `SignatureError` / `APIError(status_code,response_body)` / `CertificateError`。
- **完整单元测试**：12 个测试文件覆盖 version / formatter / utils.http / utils.pem / crypto.rsa / crypto.aes / signer / http_client / callback / certificates / factory / services。
- **使用示例**：`README.md` 覆盖 RSA 单证书、RSA 自动证书、回调解析和通用 API 调用示例，全部使用占位参数，不硬编码敏感信息。
- **项目工程化**：`pyproject.toml`（PEP 621）、`LICENSE`（Apache-2.0）、`.gitignore`、`pytest` + `pytest-httpx` + `pytest-cov` 配置、`ruff` + `mypy` 开发依赖。
