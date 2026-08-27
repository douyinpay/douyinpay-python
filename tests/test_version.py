import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from douyinpay.version import SDK_VERSION, SDK_LANG, SDK_LANG_VERSION, build_sdk_agent, USER_AGENT


FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')


def test_sdk_version_format():
    parts = SDK_VERSION.split(".")
    assert len(parts) == 3
    for p in parts:
        assert p.isdigit()


def test_build_sdk_agent_rsa():
    agent = build_sdk_agent("RSA", "80001234567")
    assert agent == f"RSA-{SDK_LANG_VERSION}-80001234567"
    assert agent.startswith("RSA-PYTHON-v")


def test_build_sdk_agent_auto_rsa():
    agent = build_sdk_agent("AutoRSA", "123")
    assert agent.startswith("AutoRSA-PYTHON-v")


def test_build_sdk_agent_sm2():
    agent = build_sdk_agent("SM2", "123")
    assert agent.startswith("SM2-PYTHON-v")


def test_build_sdk_agent_auto_sm2():
    agent = build_sdk_agent("AutoSM2", "123")
    assert agent.startswith("AutoSM2-PYTHON-v")


def test_user_agent_contains_sdk_version():
    assert SDK_VERSION in USER_AGENT
    assert "douyinpay-python/" in USER_AGENT
    assert "httpx" in USER_AGENT
