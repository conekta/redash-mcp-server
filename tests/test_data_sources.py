import json

import httpx
import pytest

from redash_mcp.tools.data_sources import (
    get_data_source,
    get_data_source_schema,
    list_data_sources,
    check_data_source_connection,
)


@pytest.mark.asyncio
async def test_list_data_sources(mock_api):
    mock_api.get("/api/data_sources").mock(
        return_value=httpx.Response(
            200, json=[{"id": 1, "name": "PostgreSQL"}]
        )
    )
    result = await list_data_sources()
    data = json.loads(result)
    assert data[0]["name"] == "PostgreSQL"


@pytest.mark.asyncio
async def test_get_data_source(mock_api):
    mock_api.get("/api/data_sources/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "PostgreSQL"})
    )
    result = await get_data_source(1)
    data = json.loads(result)
    assert data["id"] == 1


@pytest.mark.asyncio
async def test_get_data_source_schema(mock_api):
    mock_api.get("/api/data_sources/1/schema").mock(
        return_value=httpx.Response(
            200, json={"schema": [{"name": "public", "columns": []}]}
        )
    )
    result = await get_data_source_schema(1)
    data = json.loads(result)
    assert data["schema"][0]["name"] == "public"


@pytest.mark.asyncio
async def test_get_data_source_schema_refresh(mock_api):
    route = mock_api.get("/api/data_sources/1/schema").mock(
        return_value=httpx.Response(200, json={"schema": []})
    )
    await get_data_source_schema(1, refresh=True)
    assert route.calls[0].request.url.params["refresh"] == "true"


@pytest.mark.asyncio
async def test_check_data_source_connection(mock_api):
    mock_api.post("/api/data_sources/1/test").mock(
        return_value=httpx.Response(200, json={"message": "success"})
    )
    result = await check_data_source_connection(1)
    data = json.loads(result)
    assert data["message"] == "success"
