SDK_VERSION = "1.0.0"
SDK_LANG = "PYTHON"
HTTP_CLIENT_NAME = "httpx"
USER_AGENT = f"douyinpay-python/{SDK_VERSION} {HTTP_CLIENT_NAME}"
SDK_LANG_VERSION = f"{SDK_LANG}-v{SDK_VERSION}"


def build_sdk_agent(agent_type: str, mchid: str) -> str:
    return f"{agent_type}-{SDK_LANG_VERSION}-{mchid}"
