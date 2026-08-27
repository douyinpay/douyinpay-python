class DouYinPayError(Exception):
    pass


class DouYinPayInvalidArgumentError(DouYinPayError):
    pass


class DouYinPaySignatureError(DouYinPayError):
    pass


class DouYinPayAPIError(DouYinPayError):
    def __init__(self, message: str, status_code: int = 0, response_body: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class DouYinPayCertificateError(DouYinPayError):
    pass
