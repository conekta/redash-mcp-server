import json

import httpx
import pytest

from redash_mcp.tools.visualizations import list_query_visualizations


@pytest.mark.asyncio
async def test_list_query_visualizations(mock_api):
    mock_api.get("/api/queries/1").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 1,
                "visualizations": [
                    {"id": 10, "type": "TABLE"},
                    {"id": 11, "type": "CHART"},
                ],
            },
        )
    )
    result = await list_query_visualizations(1)
    data = json.loads(result)
    assert len(data) == 2
    assert data[0]["type"] == "TABLE"


@pytest.mark.asyncio
async def test_list_query_visualizations_empty(mock_api):
    mock_api.get("/api/queries/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "visualizations": []})
    )
    result = await list_query_visualizations(1)
    data = json.loads(result)
    assert data == []


@pytest.mark.asyncio
async def test_list_query_visualizations_error(mock_api):
    mock_api.get("/api/queries/1").mock(
        return_value=httpx.Response(404, json={"message": "Not found"})
    )
    result = await list_query_visualizations(1)
    data = json.loads(result)
    assert data["error"] is True
