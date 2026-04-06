import json
from unittest.mock import patch

import httpx
import pytest

from redash_mcp.tools.query_results import execute_query, execute_sql, get_query_result


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


# --- execute_sql ---

@pytest.mark.asyncio
async def test_execute_sql_sync_result(mock_api):
    mock_api.post("/api/query_results").mock(
        return_value=httpx.Response(200, json={"query_result": {"data": {"rows": [{"n": 1}]}}})
    )
    result = await execute_sql(1, "SELECT 1 AS n")
    data = json.loads(result)
    assert data["query_result"]["data"]["rows"][0]["n"] == 1


@pytest.mark.asyncio
async def test_execute_sql_async_success(mock_api):
    mock_api.post("/api/query_results").mock(
        return_value=httpx.Response(200, json={"job": {"id": "job_abc", "status": 1}})
    )
    mock_api.get("/api/jobs/job_abc").mock(
        return_value=httpx.Response(200, json={"job": {"id": "job_abc", "status": 3, "query_result_id": 99}})
    )
    mock_api.get("/api/query_results/99").mock(
        return_value=httpx.Response(200, json={"query_result": {"data": {"rows": [{"x": 7}]}}})
    )
    with patch("asyncio.sleep"):
        result = await execute_sql(1, "SELECT 7 AS x")
    data = json.loads(result)
    assert data["query_result"]["data"]["rows"][0]["x"] == 7


@pytest.mark.asyncio
async def test_execute_sql_async_error(mock_api):
    mock_api.post("/api/query_results").mock(
        return_value=httpx.Response(200, json={"job": {"id": "job_bad", "status": 1}})
    )
    mock_api.get("/api/jobs/job_bad").mock(
        return_value=httpx.Response(200, json={"job": {"id": "job_bad", "status": 4, "error": "syntax error"}})
    )
    with patch("asyncio.sleep"):
        result = await execute_sql(1, "SELECT bad")
    data = json.loads(result)
    assert data["error"] is True
    assert "syntax error" in data["message"]


@pytest.mark.asyncio
async def test_execute_sql_api_error(mock_api):
    mock_api.post("/api/query_results").mock(
        return_value=httpx.Response(403, json={"message": "Forbidden"})
    )
    result = await execute_sql(1, "SELECT 1")
    data = json.loads(result)
    assert data["error"] is True


# --- execute_query ---

@pytest.mark.asyncio
async def test_execute_query_sync_result(mock_api):
    mock_api.post("/api/queries/1/results").mock(
        return_value=httpx.Response(200, json={"query_result": {"data": {"rows": [{"n": 1}]}}})
    )
    result = await execute_query(1)
    data = json.loads(result)
    assert data["query_result"]["data"]["rows"][0]["n"] == 1


@pytest.mark.asyncio
async def test_execute_query_async_success(mock_api):
    mock_api.post("/api/queries/1/results").mock(
        return_value=httpx.Response(200, json={"job": {"id": "job_1", "status": 1}})
    )
    mock_api.get("/api/jobs/job_1").mock(
        return_value=httpx.Response(200, json={"job": {"id": "job_1", "status": 3, "query_result_id": 42}})
    )
    mock_api.get("/api/query_results/42").mock(
        return_value=httpx.Response(200, json={"query_result": {"data": {"rows": [{"count": 5}]}}})
    )
    with patch("asyncio.sleep"):
        result = await execute_query(1)
    data = json.loads(result)
    assert data["query_result"]["data"]["rows"][0]["count"] == 5


@pytest.mark.asyncio
async def test_execute_query_with_parameters(mock_api):
    route = mock_api.post("/api/queries/1/results").mock(
        return_value=httpx.Response(200, json={"job": {"id": "job_2", "status": 1}})
    )
    mock_api.get("/api/jobs/job_2").mock(
        return_value=httpx.Response(200, json={"job": {"id": "job_2", "status": 3, "query_result_id": 43}})
    )
    mock_api.get("/api/query_results/43").mock(
        return_value=httpx.Response(200, json={"query_result": {"data": {"rows": []}}})
    )
    with patch("asyncio.sleep"):
        await execute_query(1, parameters_json='{"date": "2024-01-01"}')
    sent_body = json.loads(route.calls[0].request.content)
    assert sent_body["parameters"] == {"date": "2024-01-01"}


@pytest.mark.asyncio
async def test_execute_query_invalid_parameters():
    result = await execute_query(1, parameters_json="not-json")
    data = json.loads(result)
    assert data["error"] is True


@pytest.mark.asyncio
async def test_poll_job_timeout(mock_api):
    mock_api.post("/api/query_results").mock(
        return_value=httpx.Response(200, json={"job": {"id": "job_pending", "status": 1}})
    )
    mock_api.get("/api/jobs/job_pending").mock(
        return_value=httpx.Response(200, json={"job": {"id": "job_pending", "status": 1}})
    )
    with patch("asyncio.sleep"):
        result = await execute_sql(1, "SELECT 1")
    data = json.loads(result)
    assert data["error"] is True
    assert "Timed out" in data["message"]


@pytest.mark.asyncio
async def test_poll_job_cancelled(mock_api):
    mock_api.post("/api/query_results").mock(
        return_value=httpx.Response(200, json={"job": {"id": "job_cancel", "status": 1}})
    )
    mock_api.get("/api/jobs/job_cancel").mock(
        return_value=httpx.Response(200, json={"job": {"id": "job_cancel", "status": 5}})
    )
    with patch("asyncio.sleep"):
        result = await execute_sql(1, "SELECT 1")
    data = json.loads(result)
    assert data["error"] is True


@pytest.mark.asyncio
async def test_poll_job_http_error_propagated(mock_api):
    mock_api.post("/api/query_results").mock(
        return_value=httpx.Response(200, json={"job": {"id": "job_blip", "status": 1}})
    )
    mock_api.get("/api/jobs/job_blip").mock(
        return_value=httpx.Response(500, json={"message": "Internal Server Error"})
    )
    with patch("asyncio.sleep"):
        result = await execute_sql(1, "SELECT 1")
    data = json.loads(result)
    assert data["error"] is True
    assert "Timed out" not in data.get("message", "")
