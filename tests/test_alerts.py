import json

import httpx
import pytest

from redash_mcp.tools.alerts import create_alert, get_alert, list_alerts


@pytest.mark.asyncio
async def test_list_alerts(mock_api):
    mock_api.get("/api/alerts").mock(
        return_value=httpx.Response(200, json=[{"id": 1, "name": "Alert1"}])
    )
    result = await list_alerts()
    data = json.loads(result)
    assert data[0]["name"] == "Alert1"


@pytest.mark.asyncio
async def test_get_alert(mock_api):
    mock_api.get("/api/alerts/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Alert1"})
    )
    result = await get_alert(1)
    data = json.loads(result)
    assert data["id"] == 1


@pytest.mark.asyncio
async def test_create_alert(mock_api):
    mock_api.post("/api/alerts").mock(
        return_value=httpx.Response(200, json={"id": 2, "name": "New Alert"})
    )
    result = await create_alert(
        query_id=1,
        name="New Alert",
        options_json='{"column": "count", "op": "greater than", "value": 100}',
    )
    data = json.loads(result)
    assert data["id"] == 2


@pytest.mark.asyncio
async def test_create_alert_invalid_options():
    result = await create_alert(
        query_id=1, name="Bad", options_json="not-json"
    )
    data = json.loads(result)
    assert data["error"] is True
