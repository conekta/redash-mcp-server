import json

import httpx
import pytest

from redash_mcp.tools.users import get_user, list_users


@pytest.mark.asyncio
async def test_list_users(mock_api):
    mock_api.get("/api/users").mock(
        return_value=httpx.Response(
            200, json={"count": 1, "results": [{"id": 1, "name": "Admin"}]}
        )
    )
    result = await list_users()
    data = json.loads(result)
    assert data["results"][0]["name"] == "Admin"


@pytest.mark.asyncio
async def test_list_users_pagination(mock_api):
    route = mock_api.get("/api/users").mock(
        return_value=httpx.Response(200, json={"count": 0, "results": []})
    )
    await list_users(page=2, page_size=10)
    assert route.calls[0].request.url.params["page"] == "2"
    assert route.calls[0].request.url.params["page_size"] == "10"


@pytest.mark.asyncio
async def test_get_user(mock_api):
    mock_api.get("/api/users/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Admin"})
    )
    result = await get_user(1)
    data = json.loads(result)
    assert data["id"] == 1
