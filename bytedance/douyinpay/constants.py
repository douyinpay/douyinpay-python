class Headers:
    RequestID = "Request-Id"
    Serial = "Douyinpay-Serial"
    Timestamp = "Douyinpay-Timestamp"
    Nonce = "Douyinpay-Nonce"
    Signature = "Douyinpay-Signature"
    SdkAgent = "Douyinpay-Sdk-Agent"
    UserAgent = "User-Agent"
    Authorization = "Authorization"
    Accept = "Accept"
    ContentType = "Content-Type"


class SignType:
    RSA = "RSA"
    SM2 = "SM2"


class EncryptType:
    AES = "AES"
    SM4 = "SM4"


GET_PLATFORM_CERTS_PATH = "/v1/merchant/certificates/getPlatformCertificates"

AUTHORIZATION_TYPE = "DouyinPay-RSA"

DEFAULT_BASE_URL = "https://api.douyinpay.com"
DEFAULT_MAX_CLOCK_OFFSET = 300
DEFAULT_REFRESH_INTERVAL_SEC = 24 * 60 * 60
DEFAULT_TIMEOUT = 30.0
DEFAULT_NONCE_SIZE = 32


class SdkAgentType:
    RSA = "RSA"
    AUTO_RSA = "AutoRSA"
    SM2 = "SM2"
    AUTO_SM2 = "AutoSM2"


ERR_INIT_MCHID_MANDATORY = "mchid is required"
ERR_INIT_SERIAL_MANDATORY = "serial is required"
ERR_INIT_PRIVATE_KEY_MANDATORY = "private_key is required"
ERR_INIT_CERTS_MANDATORY = "certs is required"
ERR_INIT_CERTS_EXCLUDE_MCH_SERIAL = "certs contains merchant's own serial which is not allowed"
ERR_RES_HEADERS_INCOMPLETE = "response headers incomplete"
ERR_RES_TIMESTAMP_OFFSET = "timestamp offset exceeds allowed %s seconds"
ERR_RES_PLATFORM_SERIAL_NOT_FOUND = "platform certificate serial %s not found"
ERR_RES_SIGNATURE_VERIFY_FAILED = "signature verification failed"
ERR_UNSUPPORTED_SIGN_TYPE = "unsupported sign type: %s"
ERR_UNSUPPORTED_ENCRYPT_TYPE = "unsupported encrypt type: %s"
ERR_AES_KEY_LENGTH = "AES key must be 32 bytes (256 bits)"
ERR_SM4_KEY_LENGTH = "SM4 key must be 16 bytes (128 bits)"
ERR_CALLBACK_ALGORITHM = "unsupported callback algorithm: %s"
