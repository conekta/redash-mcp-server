import json

import httpx
import pytest

from redash_mcp.tools.query_results import execute_query, get_query_result


@pytest.mark.asyncio
async def test_get_query_result(mock_api):
    mock_api.get("/api/queries/1/results").mock(
        return_value=httpx.Response(
            200,
            json={"query_result": {"data": {"rows": [{"count": 42}]}}},
        )
    )
    result = await get_query_result(1)
    data = json.loads(result)
    assert data["query_result"]["data"]["rows"][0]["count"] == 42


@pytest.mark.asyncio
async def test_execute_query(mock_api):
    mock_api.post("/api/query_results").mock(
        return_value=httpx.Response(200, json={"job": {"id": "job_1"}})
    )
    result = await execute_query(1)
    data = json.loads(result)
    assert data["job"]["id"] == "job_1"


@pytest.mark.asyncio
async def test_execute_query_with_parameters(mock_api):
    route = mock_api.post("/api/query_results").mock(
        return_value=httpx.Response(200, json={"job": {"id": "job_2"}})
    )
    await execute_query(1, parameters_json='{"date": "2024-01-01"}')
    sent_body = json.loads(route.calls[0].request.content)
    assert sent_body["parameters"] == {"date": "2024-01-01"}


@pytest.mark.asyncio
async def test_execute_query_invalid_parameters():
    result = await execute_query(1, parameters_json="not-json")
    data = json.loads(result)
    assert data["error"] is True
