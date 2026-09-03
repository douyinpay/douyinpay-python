# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: Apache-2.0

class DouYinPayError(Exception):
    pass


class DouYinPayInvalidArgumentError(DouYinPayError):
    pass


class DouYinPaySignatureError(DouYinPayError):
    pass


class DouYinPayCertificateSerialNotFound(DouYinPaySignatureError):
    def __init__(self, serial: str, message: str = ""):
        super().__init__(message or f"platform certificate serial {serial} not found")
        self.serial = serial


class DouYinPayAPIError(DouYinPayError):
    def __init__(self, message: str, status_code: int = 0, response_body: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class DouYinPayCertificateError(DouYinPayError):
    pass
