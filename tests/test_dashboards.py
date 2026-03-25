import json

import httpx
import pytest

from redash_mcp.tools.dashboards import (
    create_dashboard,
    get_dashboard,
    list_dashboards,
    update_dashboard,
)


@pytest.mark.asyncio
async def test_list_dashboards(mock_api):
    mock_api.get("/api/dashboards").mock(
        return_value=httpx.Response(
            200, json={"count": 1, "results": [{"id": 1, "name": "D1"}]}
        )
    )
    result = await list_dashboards()
    data = json.loads(result)
    assert data["results"][0]["id"] == 1


@pytest.mark.asyncio
async def test_list_dashboards_with_search(mock_api):
    route = mock_api.get("/api/dashboards").mock(
        return_value=httpx.Response(200, json={"count": 0, "results": []})
    )
    await list_dashboards(search="sales")
    assert route.calls[0].request.url.params["q"] == "sales"


@pytest.mark.asyncio
async def test_get_dashboard(mock_api):
    mock_api.get("/api/dashboards/my-dashboard").mock(
        return_value=httpx.Response(200, json={"id": 1, "slug": "my-dashboard"})
    )
    result = await get_dashboard("my-dashboard")
    data = json.loads(result)
    assert data["slug"] == "my-dashboard"


@pytest.mark.asyncio
async def test_create_dashboard(mock_api):
    mock_api.post("/api/dashboards").mock(
        return_value=httpx.Response(200, json={"id": 2, "name": "New"})
    )
    result = await create_dashboard("New")
    data = json.loads(result)
    assert data["id"] == 2


@pytest.mark.asyncio
async def test_update_dashboard(mock_api):
    mock_api.post("/api/dashboards/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Updated"})
    )
    result = await update_dashboard(1, name="Updated")
    data = json.loads(result)
    assert data["name"] == "Updated"


@pytest.mark.asyncio
async def test_update_dashboard_with_tags(mock_api):
    route = mock_api.post("/api/dashboards/1").mock(
        return_value=httpx.Response(200, json={"id": 1})
    )
    await update_dashboard(1, tags_json='["tag1", "tag2"]')
    sent_body = json.loads(route.calls[0].request.content)
    assert sent_body["tags"] == ["tag1", "tag2"]


@pytest.mark.asyncio
async def test_update_dashboard_no_fields():
    result = await update_dashboard(1)
    data = json.loads(result)
    assert data["error"] is True
