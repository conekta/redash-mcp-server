import json

import httpx
import pytest
import respx
from mcp.server.lowlevel.server import request_ctx
from mcp.shared.context import RequestContext
from starlette.requests import Request

from redash_mcp import auth
from redash_mcp.client import USER_AGENT, get_client, redash_get, redash_request


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


def test_get_client_sets_default_headers():
    client = get_client()
    assert client.headers["accept"] == "application/json"
    assert "authorization" not in client.headers
    assert client.headers["user-agent"] == USER_AGENT


@pytest.mark.asyncio
async def test_redash_get_missing_key(monkeypatch):
    monkeypatch.delenv("REDASH_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="REDASH_API_KEY environment variable"):
        await redash_get("/api/queries")


def test_redash_request_uses_authorization_header_from_request_context():
    auth.set_api_key_provider(auth.get_request_header_api_key)
    request = _request_with_headers([(b"authorization", b"Key key_from_header")])
    token = request_ctx.set(
        RequestContext(
            request_id="req_1",
            meta=None,
            session=None,
            lifespan_context=None,
            request=request,
        )
    )

    try:
        assert get_client().headers.get("authorization") is None
        assert auth.get_api_key() == "key_from_header"
    finally:
        request_ctx.reset(token)


@pytest.mark.asyncio
async def test_redash_request_sends_request_authorization_header(mock_api):
    auth.set_api_key_provider(auth.get_request_header_api_key)
    route = mock_api.get("/api/queries").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    request = _request_with_headers([(b"authorization", b"Key key_from_header")])
    token = request_ctx.set(
        RequestContext(
            request_id="req_2",
            meta=None,
            session=None,
            lifespan_context=None,
            request=request,
        )
    )

    try:
        await redash_get("/api/queries")
    finally:
        request_ctx.reset(token)

    assert len(route.calls) == 1
    sent_request = route.calls[0].request
    assert sent_request.headers["authorization"] == "Key key_from_header"
    assert sent_request.headers["user-agent"] == USER_AGENT


def test_request_header_provider_requires_key_format():
    auth.set_api_key_provider(auth.get_request_header_api_key)
    request = _request_with_headers([(b"authorization", b"Bearer key_from_header")])
    token = request_ctx.set(
        RequestContext(
            request_id="req_3",
            meta=None,
            session=None,
            lifespan_context=None,
            request=request,
        )
    )

    try:
        with pytest.raises(RuntimeError, match="Key token format"):
            auth.get_api_key()
    finally:
        request_ctx.reset(token)


@pytest.mark.asyncio
async def test_redash_get_success(mock_api):
    mock_api.get("/api/queries").mock(
        return_value=httpx.Response(200, json={"results": [{"id": 1}]})
    )
    result = await redash_get("/api/queries")
    data = json.loads(result)
    assert data["results"][0]["id"] == 1


@pytest.mark.asyncio
async def test_redash_get_http_error(mock_api):
    mock_api.get("/api/queries").mock(
        return_value=httpx.Response(401, json={"message": "Unauthorized"})
    )
    result = await redash_get("/api/queries")
    data = json.loads(result)
    assert data["error"] is True
    assert data["status_code"] == 401


@pytest.mark.asyncio
async def test_redash_request_post_success(mock_api):
    mock_api.post("/api/queries").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Test"})
    )
    result = await redash_request("POST", "/api/queries", body={"name": "Test"})
    data = json.loads(result)
    assert data["id"] == 1


@pytest.mark.asyncio
async def test_redash_request_422_error(mock_api):
    mock_api.post("/api/queries").mock(
        return_value=httpx.Response(
            422, json={"message": "Validation error"}
        )
    )
    result = await redash_request("POST", "/api/queries", body={"name": "Bad"})
    data = json.loads(result)
    assert data["error"] is True
    assert data["status_code"] == 422


@pytest.mark.asyncio
async def test_redash_request_204_no_content(mock_api):
    mock_api.delete("/api/queries/1").mock(
        return_value=httpx.Response(204)
    )
    result = await redash_request("DELETE", "/api/queries/1")
    data = json.loads(result)
    assert data["success"] is True


@pytest.mark.asyncio
async def test_redash_request_sends_json_body(mock_api):
    route = mock_api.post("/api/queries").mock(
        return_value=httpx.Response(200, json={"id": 1})
    )
    body = {"name": "Test", "query": "SELECT 1", "data_source_id": 1}
    await redash_request("POST", "/api/queries", body=body)

    assert len(route.calls) == 1
    request = route.calls[0].request
    sent_body = json.loads(request.content)
    assert sent_body == body
    assert request.headers["content-type"] == "application/json"
