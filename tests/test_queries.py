import json
from unittest.mock import patch

import httpx
import pytest

from redash_mcp.tools.queries import (
    archive_query,
    create_query,
    get_query,
    get_recent_queries,
    list_queries,
    refresh_query,
    search_queries,
    update_query,
)

_QUERY_API_KEY = "qry_test_key_do_not_leak"
_AUTHOR_EMAIL = "casey@example.com"
_EDITOR_EMAIL = "riley@example.com"
_AVATAR_URL = "https://example.com/avatar.png"
_COMPACT_KEYS = {
    "id",
    "name",
    "description",
    "data_source_id",
    "tags",
    "updated_at",
    "is_archived",
    "is_draft",
    "author",
}


def _full_query(**overrides):
    query = {
        "id": 7,
        "latest_query_data_id": 99,
        "name": "Daily totals",
        "description": "Fictional totals",
        "query": "SELECT 1 AS total",
        "query_hash": "abc123",
        "schedule": None,
        "api_key": _QUERY_API_KEY,
        "is_archived": False,
        "is_draft": True,
        "updated_at": "2026-01-02T03:04:05Z",
        "created_at": "2026-01-01T00:00:00Z",
        "data_source_id": 3,
        "options": {},
        "version": 2,
        "tags": ["demo"],
        "is_safe": True,
        "user": {
            "id": 4,
            "name": "Casey Example",
            "email": _AUTHOR_EMAIL,
            "profile_image_url": _AVATAR_URL,
            "groups": [1],
        },
        "last_modified_by": {
            "id": 5,
            "name": "Riley Example",
            "email": _EDITOR_EMAIL,
            "profile_image_url": _AVATAR_URL,
            "groups": [2],
        },
        "visualizations": [{"id": 8, "type": "TABLE", "name": "Table"}],
        "is_favorite": False,
        "can_edit": True,
    }
    query.update(overrides)
    return query


def _walk_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _walk_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


def _assert_no_secrets(raw, data):
    keys = set(_walk_keys(data))
    assert "api_key" not in keys
    assert "email" not in keys
    for secret in (_QUERY_API_KEY, _AUTHOR_EMAIL, _EDITOR_EMAIL, _AVATAR_URL):
        assert secret not in raw


def _page(query):
    return {"count": 1, "page": 2, "page_size": 25, "results": [query]}


async def _call_list_tool(tool, include_query=None):
    if tool == "list":
        if include_query is None:
            return await list_queries()
        return await list_queries(include_query=include_query)
    if tool == "search":
        if include_query is None:
            return await search_queries("totals")
        return await search_queries("totals", include_query=include_query)
    if include_query is None:
        return await get_recent_queries()
    return await get_recent_queries(include_query=include_query)


@pytest.mark.asyncio
async def test_list_queries(mock_api):
    mock_api.get("/api/queries").mock(
        return_value=httpx.Response(
            200, json={"count": 1, "results": [{"id": 1, "name": "Q1"}]}
        )
    )
    result = await list_queries()
    data = json.loads(result)
    assert data["results"][0]["id"] == 1


@pytest.mark.asyncio
async def test_list_queries_with_search(mock_api):
    route = mock_api.get("/api/queries").mock(
        return_value=httpx.Response(200, json={"count": 0, "results": []})
    )
    await list_queries(search="revenue")
    assert route.calls[0].request.url.params["q"] == "revenue"


@pytest.mark.asyncio
async def test_get_query(mock_api):
    mock_api.get("/api/queries/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Q1"})
    )
    result = await get_query(1)
    data = json.loads(result)
    assert data["id"] == 1


@pytest.mark.asyncio
async def test_create_query(mock_api):
    mock_api.post("/api/queries").mock(
        return_value=httpx.Response(200, json={"id": 2, "name": "New Query"})
    )
    result = await create_query(
        name="New Query", query="SELECT 1", data_source_id=1
    )
    data = json.loads(result)
    assert data["id"] == 2


@pytest.mark.asyncio
async def test_create_query_with_schedule(mock_api):
    route = mock_api.post("/api/queries").mock(
        return_value=httpx.Response(200, json={"id": 3})
    )
    await create_query(
        name="Scheduled",
        query="SELECT 1",
        data_source_id=1,
        schedule_json='{"interval": 3600}',
    )
    sent_body = json.loads(route.calls[0].request.content)
    assert sent_body["schedule"] == {"interval": 3600}


@pytest.mark.asyncio
async def test_create_query_invalid_schedule():
    result = await create_query(
        name="Bad", query="SELECT 1", data_source_id=1, schedule_json="not-json"
    )
    data = json.loads(result)
    assert data["error"] is True


@pytest.mark.asyncio
async def test_create_query_with_description(mock_api):
    route = mock_api.post("/api/queries").mock(
        return_value=httpx.Response(200, json={"id": 4})
    )
    await create_query(
        name="Described",
        query="SELECT 1",
        data_source_id=1,
        description="Fictional description",
    )
    sent_body = json.loads(route.calls[0].request.content)
    assert sent_body["description"] == "Fictional description"


@pytest.mark.asyncio
async def test_update_query(mock_api):
    mock_api.post("/api/queries/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Updated"})
    )
    result = await update_query(1, name="Updated")
    data = json.loads(result)
    assert data["name"] == "Updated"


@pytest.mark.asyncio
async def test_update_query_no_fields():
    result = await update_query(1)
    data = json.loads(result)
    assert data["error"] is True


@pytest.mark.asyncio
async def test_update_query_invalid_schedule():
    result = await update_query(1, schedule_json="not-json")
    data = json.loads(result)
    assert data["error"] is True


@pytest.mark.asyncio
async def test_search_queries(mock_api):
    route = mock_api.get("/api/queries").mock(
        return_value=httpx.Response(
            200, json={"count": 1, "results": [{"id": 1, "name": "Q1"}]}
        )
    )
    await search_queries("revenue")
    assert route.calls[0].request.url.params["q"] == "revenue"


@pytest.mark.asyncio
async def test_search_queries_no_results(mock_api):
    mock_api.get("/api/queries").mock(
        return_value=httpx.Response(200, json={"count": 0, "results": []})
    )
    result = await search_queries("missing")
    data = json.loads(result)
    assert data["count"] == 0
    assert data["results"] == []


@pytest.mark.asyncio
async def test_get_recent_queries(mock_api):
    mock_api.get("/api/queries/recent").mock(
        return_value=httpx.Response(200, json=[{"id": 1}])
    )
    result = await get_recent_queries()
    data = json.loads(result)
    assert data[0]["id"] == 1


@pytest.mark.asyncio
async def test_archive_query(mock_api):
    mock_api.delete("/api/queries/1").mock(
        return_value=httpx.Response(204)
    )
    result = await archive_query(1)
    data = json.loads(result)
    assert data["success"] is True


@pytest.mark.asyncio
async def test_refresh_query(mock_api):
    mock_api.post("/api/queries/1/results").mock(
        return_value=httpx.Response(200, json={"job": {"id": "job_1", "status": 1}})
    )
    mock_api.get("/api/jobs/job_1").mock(
        return_value=httpx.Response(200, json={"job": {"id": "job_1", "status": 3, "query_result_id": 10}})
    )
    mock_api.get("/api/query_results/10").mock(
        return_value=httpx.Response(200, json={"query_result": {"data": {"rows": [{"n": 1}]}}})
    )
    with patch("asyncio.sleep"):
        result = await refresh_query(1)
    data = json.loads(result)
    assert data["query_result"]["data"]["rows"][0]["n"] == 1


@pytest.mark.parametrize(
    ("tool", "path", "kind"),
    [
        ("list", "/api/queries", "page"),
        ("search", "/api/queries", "page"),
        ("recent", "/api/queries/recent", "list"),
    ],
)
@pytest.mark.asyncio
async def test_query_lists_are_compact(mock_api, tool, path, kind):
    body = _page(_full_query()) if kind == "page" else [_full_query()]
    route = mock_api.get(path).mock(return_value=httpx.Response(200, json=body))
    raw = await _call_list_tool(tool)
    if tool == "search":
        assert route.calls[0].request.url.params["q"] == "totals"
    data = json.loads(raw)
    if kind == "page":
        assert data["count"] == 1
        assert data["page"] == 2
        assert data["page_size"] == 25
        items = data["results"]
    else:
        items = data
    item = items[0]
    assert set(item) == _COMPACT_KEYS
    assert item["id"] == 7
    assert item["name"] == "Daily totals"
    assert item["description"] == "Fictional totals"
    assert item["data_source_id"] == 3
    assert item["tags"] == ["demo"]
    assert item["updated_at"] == "2026-01-02T03:04:05Z"
    assert item["is_archived"] is False
    assert item["is_draft"] is True
    assert item["author"] == "Casey Example"
    assert "query" not in item
    _assert_no_secrets(raw, data)


@pytest.mark.parametrize(
    ("tool", "path", "kind"),
    [
        ("list", "/api/queries", "page"),
        ("search", "/api/queries", "page"),
        ("recent", "/api/queries/recent", "list"),
    ],
)
@pytest.mark.asyncio
async def test_query_lists_include_query(mock_api, tool, path, kind):
    body = _page(_full_query()) if kind == "page" else [_full_query()]
    route = mock_api.get(path).mock(return_value=httpx.Response(200, json=body))
    raw = await _call_list_tool(tool, include_query=True)
    if tool == "search":
        assert route.calls[0].request.url.params["q"] == "totals"
    data = json.loads(raw)
    items = data["results"] if kind == "page" else data
    assert set(items[0]) == _COMPACT_KEYS | {"query"}
    assert items[0]["query"] == "SELECT 1 AS total"
    assert items[0]["author"] == "Casey Example"
    _assert_no_secrets(raw, data)


@pytest.mark.parametrize(
    ("method", "path", "invoke"),
    [
        ("get", "/api/queries/7", lambda: get_query(7)),
        (
            "post",
            "/api/queries",
            lambda: create_query("Daily totals", "SELECT 1 AS total", 3),
        ),
        ("post", "/api/queries/7", lambda: update_query(7, name="Daily totals")),
    ],
    ids=["get", "create", "update"],
)
@pytest.mark.asyncio
async def test_query_writes_are_sanitized(mock_api, method, path, invoke):
    getattr(mock_api, method)(path).mock(
        return_value=httpx.Response(200, json=_full_query())
    )
    raw = await invoke()
    data = json.loads(raw)
    _assert_no_secrets(raw, data)
    assert data["id"] == 7
    assert data["query"] == "SELECT 1 AS total"
    assert data["query_hash"] == "abc123"
    assert data["user"] == {"id": 4, "name": "Casey Example"}
    assert data["last_modified_by"] == {"id": 5, "name": "Riley Example"}
    assert data["visualizations"] == [{"id": 8, "type": "TABLE", "name": "Table"}]
    assert "api_key" not in data


@pytest.mark.asyncio
async def test_list_queries_error_passthrough(mock_api):
    mock_api.get("/api/queries").mock(
        return_value=httpx.Response(502, json={"detail": "unavailable"})
    )
    raw = await list_queries()
    assert json.loads(raw) == {
        "error": True,
        "status_code": 502,
        "message": "Redash API error: 502",
        "details": {"detail": "unavailable"},
    }


@pytest.mark.asyncio
async def test_get_query_error_passthrough(mock_api):
    mock_api.get("/api/queries/7").mock(
        return_value=httpx.Response(404, json={"message": "missing"})
    )
    raw = await get_query(7)
    assert json.loads(raw) == {
        "error": True,
        "status_code": 404,
        "message": "Redash API error: 404",
        "details": {"message": "missing"},
    }


@pytest.mark.asyncio
async def test_list_queries_invalid_json_passthrough(monkeypatch):
    async def fake_get(path, params=None):
        return "not-json"

    monkeypatch.setattr("redash_mcp.tools.queries.redash_get", fake_get)
    assert await list_queries() == "not-json"


@pytest.mark.asyncio
async def test_get_query_invalid_json_passthrough(monkeypatch):
    async def fake_get(path, params=None):
        return "not-json"

    monkeypatch.setattr("redash_mcp.tools.queries.redash_get", fake_get)
    assert await get_query(7) == "not-json"


@pytest.mark.asyncio
async def test_list_queries_missing_fields(mock_api):
    mock_api.get("/api/queries").mock(
        return_value=httpx.Response(
            200,
            json=_page(
                {
                    "id": 9,
                    "name": "Bare",
                    "api_key": _QUERY_API_KEY,
                    "user": {"id": 4, "email": _AUTHOR_EMAIL},
                }
            ),
        )
    )
    raw = await list_queries()
    data = json.loads(raw)
    item = data["results"][0]
    assert data["page"] == 2
    assert item["author"] is None
    assert item["description"] is None
    assert "query" not in item
    _assert_no_secrets(raw, data)


@pytest.mark.asyncio
async def test_recent_queries_missing_fields(mock_api):
    mock_api.get("/api/queries/recent").mock(
        return_value=httpx.Response(200, json=[{"id": 9, "name": "Bare"}])
    )
    raw = await get_recent_queries()
    data = json.loads(raw)
    assert data[0]["author"] is None
    assert data[0]["id"] == 9
    assert "query" not in data[0]


@pytest.mark.asyncio
async def test_get_query_missing_fields(mock_api):
    mock_api.get("/api/queries/9").mock(
        return_value=httpx.Response(
            200,
            json={"id": 9, "name": "Bare", "query": "SELECT 1", "api_key": _QUERY_API_KEY},
        )
    )
    raw = await get_query(9)
    data = json.loads(raw)
    assert data["id"] == 9
    assert data["query"] == "SELECT 1"
    assert "user" not in data
    assert "last_modified_by" not in data
    _assert_no_secrets(raw, data)


@pytest.mark.asyncio
async def test_get_query_non_dict_user(mock_api):
    mock_api.get("/api/queries/9").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 9,
                "name": "Bare",
                "api_key": _QUERY_API_KEY,
                "user": None,
                "last_modified_by": "not-a-user",
            },
        )
    )
    raw = await get_query(9)
    data = json.loads(raw)
    assert data["user"] is None
    assert data["last_modified_by"] is None
    _assert_no_secrets(raw, data)


@pytest.mark.asyncio
async def test_list_queries_non_dict_result(mock_api):
    mock_api.get("/api/queries").mock(
        return_value=httpx.Response(
            200,
            json={
                "count": 2,
                "page": 1,
                "page_size": 25,
                "results": [_full_query(), "not-an-object"],
            },
        )
    )
    raw = await list_queries()
    data = json.loads(raw)
    assert set(data["results"][0]) == _COMPACT_KEYS
    assert data["results"][1] == "not-an-object"
    assert data["count"] == 2
    _assert_no_secrets(raw, data)


@pytest.mark.asyncio
async def test_list_queries_single_object_is_compact(mock_api):
    mock_api.get("/api/queries").mock(
        return_value=httpx.Response(200, json=_full_query())
    )
    raw = await list_queries()
    data = json.loads(raw)
    assert set(data) == _COMPACT_KEYS
    assert data["author"] == "Casey Example"
    _assert_no_secrets(raw, data)


@pytest.mark.asyncio
async def test_list_queries_non_object_json_passthrough(monkeypatch):
    async def fake_get(path, params=None):
        return "1"

    monkeypatch.setattr("redash_mcp.tools.queries.redash_get", fake_get)
    assert await list_queries() == "1"


def test_compact_query_tool_docstrings():
    for tool in (list_queries, search_queries, get_recent_queries):
        doc = tool.__doc__ or ""
        assert "include_query" in doc
        assert "get_query" in doc
