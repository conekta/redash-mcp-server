import pytest
from mcp.server.lowlevel.server import request_ctx
from mcp.shared.context import RequestContext
from starlette.requests import Request

from redash_mcp import auth


def _request_with_headers(headers: list[tuple[bytes, bytes]]) -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/mcp",
            "headers": headers,
            "query_string": b"",
            "scheme": "https",
            "http_version": "1.1",
            "client": ("127.0.0.1", 1234),
            "server": ("testserver", 443),
        }
    )


def test_get_env_api_key_returns_env_value(monkeypatch):
    monkeypatch.setenv("REDASH_API_KEY", "env_key")

    assert auth.get_env_api_key() == "env_key"


def test_get_env_api_key_requires_env_var(monkeypatch):
    monkeypatch.delenv("REDASH_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="REDASH_API_KEY environment variable"):
        auth.get_env_api_key()


def test_get_request_header_api_key_requires_request_context():
    with pytest.raises(RuntimeError, match=auth.REQUEST_API_KEY_ERROR):
        auth.get_request_header_api_key()


def test_get_request_header_api_key_requires_request():
    token = request_ctx.set(
        RequestContext(
            request_id="req_missing_request",
            meta=None,
            session=None,
            lifespan_context=None,
            request=None,
        )
    )

    try:
        with pytest.raises(RuntimeError, match=auth.REQUEST_API_KEY_ERROR):
            auth.get_request_header_api_key()
    finally:
        request_ctx.reset(token)


def test_get_request_header_api_key_requires_authorization_header():
    request = _request_with_headers([])
    token = request_ctx.set(
        RequestContext(
            request_id="req_missing_header",
            meta=None,
            session=None,
            lifespan_context=None,
            request=request,
        )
    )

    try:
        with pytest.raises(RuntimeError, match=auth.REQUEST_API_KEY_ERROR):
            auth.get_request_header_api_key()
    finally:
        request_ctx.reset(token)


def test_get_request_header_api_key_returns_key_token():
    request = _request_with_headers([(b"authorization", b"Key header_key")])
    token = request_ctx.set(
        RequestContext(
            request_id="req_key_header",
            meta=None,
            session=None,
            lifespan_context=None,
            request=request,
        )
    )

    try:
        assert auth.get_request_header_api_key() == "header_key"
    finally:
        request_ctx.reset(token)


def test_get_request_header_api_key_rejects_non_key_tokens():
    request = _request_with_headers([(b"authorization", b"Bearer header_key")])
    token = request_ctx.set(
        RequestContext(
            request_id="req_invalid_scheme",
            meta=None,
            session=None,
            lifespan_context=None,
            request=request,
        )
    )

    try:
        with pytest.raises(RuntimeError, match="Key token format"):
            auth.get_request_header_api_key()
    finally:
        request_ctx.reset(token)


def test_get_api_key_uses_configured_provider():
    auth.set_api_key_provider(lambda: "provider_key")

    try:
        assert auth.get_api_key() == "provider_key"
    finally:
        auth.reset_api_key_provider()
