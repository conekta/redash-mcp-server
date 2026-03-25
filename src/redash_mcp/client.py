import json
import os
from importlib.metadata import PackageNotFoundError, version

import httpx

from redash_mcp.auth import get_api_key


def _get_base_url() -> str:
    url = os.environ.get("REDASH_URL", "http://localhost:5000")
    return url.rstrip("/")


def _get_user_agent() -> str:
    try:
        package_version = version("redash-mcp")
    except PackageNotFoundError:
        package_version = "unknown"
    return f"redash-mcp/{package_version}"


USER_AGENT = _get_user_agent()

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=_get_base_url(),
            headers={
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
            },
            timeout=30.0,
        )
    return _client


def _format(data: dict | list | str) -> str:
    if isinstance(data, str):
        return data
    return json.dumps(data, indent=2, ensure_ascii=False)


def _try_parse_json(text: str) -> dict | str:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return text


def build_params(**kwargs) -> dict:
    return {k: v for k, v in kwargs.items() if v is not None}


async def redash_get(path: str, params: dict | None = None) -> str:
    try:
        response = await get_client().get(
            path,
            params=params,
            headers={"Authorization": f"Key {get_api_key()}"},
        )
        response.raise_for_status()
        return _format(response.json())
    except httpx.HTTPStatusError as e:
        return _format({
            "error": True,
            "status_code": e.response.status_code,
            "message": f"Redash API error: {e.response.status_code}",
            "details": _try_parse_json(e.response.text),
        })
    except httpx.RequestError as e:
        return _format({"error": True, "message": f"Request failed: {e}"})


async def redash_request(
    method: str,
    path: str,
    body: dict | None = None,
    params: dict | None = None,
) -> str:
    try:
        response = await get_client().request(
            method,
            path,
            json=body,
            params=params,
            headers={"Authorization": f"Key {get_api_key()}"},
        )
        response.raise_for_status()
        if response.status_code == 204:
            return _format({"success": True})
        return _format(response.json())
    except httpx.HTTPStatusError as e:
        return _format({
            "error": True,
            "status_code": e.response.status_code,
            "message": f"Redash API error: {e.response.status_code}",
            "details": _try_parse_json(e.response.text),
        })
    except httpx.RequestError as e:
        return _format({"error": True, "message": f"Request failed: {e}"})
