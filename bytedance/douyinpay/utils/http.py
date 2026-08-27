import os
from urllib.parse import urlparse, urlencode, parse_qsl, urlunparse
from typing import Union, Dict, List, Any, Optional


def normalize_base_url(base_url: str) -> str:
    if not base_url:
        return base_url
    return base_url.rstrip("/")


def join_url(base_url: str, path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    base = normalize_base_url(base_url)
    if not path.startswith("/"):
        path = "/" + path
    return base + path


def _to_query_value(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def append_query(url: str, query: Optional[Union[Dict[str, Any], List[tuple]]] = None) -> str:
    if not query:
        return url
    parsed = urlparse(url)
    existing = parse_qsl(parsed.query, keep_blank_values=True)
    if isinstance(query, dict):
        items = list(query.items())
    else:
        items = list(query)
    new_pairs: List[tuple] = []
    for k, v in items:
        if v is None:
            continue
        if isinstance(v, (list, tuple)):
            for item in v:
                if item is None:
                    continue
                new_pairs.append((k, _to_query_value(item)))
        else:
            new_pairs.append((k, _to_query_value(v)))
    all_pairs = existing + new_pairs
    new_query = urlencode(all_pairs)
    parts = list(parsed)
    parts[4] = new_query
    return urlunparse(parts)


def request_target_from_url(url: str) -> str:
    parsed = urlparse(url)
    target = parsed.path or "/"
    if parsed.query:
        target = f"{target}?{parsed.query}"
    return target


def header_value(headers: Dict[str, Any], name: str) -> Optional[Any]:
    if not headers:
        return None
    target = name.lower()
    for k, v in headers.items():
        if isinstance(k, str) and k.lower() == target:
            return v
    return None


def buffer_to_str(data: Union[bytes, str, None]) -> str:
    if data is None:
        return ""
    if isinstance(data, bytes):
        return data.decode("utf-8")
    return str(data)
