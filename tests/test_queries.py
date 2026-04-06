import json

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
async def test_search_queries(mock_api):
    route = mock_api.get("/api/queries/search").mock(
        return_value=httpx.Response(200, json={"count": 0, "results": []})
    )
    await search_queries("revenue")
    assert route.calls[0].request.url.params["q"] == "revenue"


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
    from unittest.mock import patch
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
