import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from bytedance.douyinpay.utils.http import (
    normalize_base_url, join_url, append_query, request_target_from_url,
    header_value, buffer_to_str,
)


def test_normalize_base_url_strip_slash():
    assert normalize_base_url("https://a.com/") == "https://a.com"
    assert normalize_base_url("https://a.com") == "https://a.com"


def test_join_url_absolute_passthrough():
    assert join_url("https://a.com", "https://b.com/p") == "https://b.com/p"


def test_join_url_relative():
    assert join_url("https://a.com/", "v1/xx") == "https://a.com/v1/xx"
    assert join_url("https://a.com", "/v1/xx") == "https://a.com/v1/xx"


def test_append_query_simple():
    out = append_query("https://a.com/p", {"a": 1, "b": "x"})
    assert "a=1" in out and "b=x" in out


def test_append_query_array():
    out = append_query("https://a.com/p", {"ids": [1, 2]})
    assert out.count("ids=") == 2


def test_append_query_skips_none_values():
    out = append_query("https://a.com/p", {"a": None, "b": [1, None, 2]})
    assert "a=" not in out
    assert "None" not in out
    assert "b=1" in out and "b=2" in out


def test_append_query_preserve_existing():
    out = append_query("https://a.com/p?x=1", {"y": 2})
    assert "x=1" in out and "y=2" in out


def test_request_target_from_url():
    t = request_target_from_url("https://api.test.com/v1/orders?page=1")
    assert t == "/v1/orders?page=1"
    t2 = request_target_from_url("https://api.test.com/v1/orders")
    assert t2 == "/v1/orders"


def test_header_value_case_insensitive():
    h = {"Content-Type": "x", "content-length": "10"}
    assert header_value(h, "content-type") == "x"
    assert header_value(h, "Content-Length") == "10"
    assert header_value(h, "X-Missing") is None


def test_buffer_to_str():
    assert buffer_to_str(b"abc") == "abc"
    assert buffer_to_str("x") == "x"
    assert buffer_to_str(None) == ""
