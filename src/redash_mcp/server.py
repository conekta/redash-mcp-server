import os

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


def _get_env(name: str, default: str) -> str:
    return os.getenv(name, default)


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value is not None else default


def _normalize_path(path: str) -> str:
    if not path:
        return "/"
    return path if path.startswith("/") else f"/{path}"


mcp = FastMCP(
    "redash",
    instructions=(
        "Redash API server. Provides tools to manage queries, dashboards, "
        "data sources, query results, users, alerts, and visualizations. "
        "Requires a Redash API key either via Authorization Key header or "
        "REDASH_API_KEY environment variable."
    ),
    host=_get_env("REDASH_MCP_HOST", "127.0.0.1"),
    port=_get_int_env("REDASH_MCP_PORT", 8000),
    streamable_http_path=_normalize_path(
        _get_env("REDASH_MCP_STREAMABLE_HTTP_PATH", "/mcp")
    ),
)


@mcp.custom_route("/ping", methods=["GET"], include_in_schema=False)
async def ping(_: Request) -> Response:
    return JSONResponse({"status": "ok"})
