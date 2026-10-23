import json

from redash_mcp.client import build_params, redash_get, redash_request
from redash_mcp.jobs import handle_query_result_response
from redash_mcp.server import mcp
from redash_mcp.tools.query_view import compact_query_response, sanitize_query_response


@mcp.tool()
async def list_queries(
    page: int = 1,
    page_size: int = 25,
    search: str | None = None,
    include_query: bool = False,
) -> str:
    """List saved queries. Compact by default; pass include_query or call get_query for the full SQL."""
    params = build_params(page=page, page_size=page_size, q=search)
    return compact_query_response(
        await redash_get("/api/queries", params=params),
        include_query=include_query,
    )


@mcp.tool()
async def get_query(query_id: int) -> str:
    """Get a specific query by its ID."""
    return sanitize_query_response(await redash_get(f"/api/queries/{query_id}"))


@mcp.tool()
async def create_query(
    name: str,
    query: str,
    data_source_id: int,
    description: str | None = None,
    schedule_json: str | None = None,
) -> str:
    """Create a new query.

    Args:
        name: Name of the query.
        query: The SQL query string.
        data_source_id: ID of the data source to run the query against.
        description: Optional description of the query.
        schedule_json: Optional JSON string with schedule config,
            e.g. '{"interval": 3600, "until": null}'.
    """
    body: dict = {
        "name": name,
        "query": query,
        "data_source_id": data_source_id,
    }
    if description is not None:
        body["description"] = description
    if schedule_json is not None:
        try:
            body["schedule"] = json.loads(schedule_json)
        except json.JSONDecodeError:
            return json.dumps({"error": True, "message": "Invalid schedule_json"})
    return sanitize_query_response(
        await redash_request("POST", "/api/queries", body=body)
    )


@mcp.tool()
async def update_query(
    query_id: int,
    name: str | None = None,
    query: str | None = None,
    description: str | None = None,
    schedule_json: str | None = None,
) -> str:
    """Update an existing query.

    Args:
        query_id: ID of the query to update.
        name: New name for the query.
        query: New SQL query string.
        description: New description.
        schedule_json: Optional JSON string with schedule config.
    """
    body = build_params(name=name, query=query, description=description)
    if schedule_json is not None:
        try:
            body["schedule"] = json.loads(schedule_json)
        except json.JSONDecodeError:
            return json.dumps({"error": True, "message": "Invalid schedule_json"})
    if not body:
        return json.dumps({"error": True, "message": "No fields to update."})
    return sanitize_query_response(
        await redash_request("POST", f"/api/queries/{query_id}", body=body)
    )


@mcp.tool()
async def search_queries(q: str, include_query: bool = False) -> str:
    """Search queries by name or description. Compact by default; pass include_query or call get_query for the full SQL."""
    return compact_query_response(
        await redash_get("/api/queries", params={"q": q}),
        include_query=include_query,
    )


@mcp.tool()
async def get_recent_queries(include_query: bool = False) -> str:
    """Get recently executed queries. Compact by default; pass include_query or call get_query for the full SQL."""
    return compact_query_response(
        await redash_get("/api/queries/recent"),
        include_query=include_query,
    )


@mcp.tool()
async def archive_query(query_id: int) -> str:
    """Archive (soft-delete) a query."""
    return await redash_request("DELETE", f"/api/queries/{query_id}")


@mcp.tool()
async def refresh_query(query_id: int) -> str:
    """Trigger a query execution and return the result."""
    raw = await redash_request("POST", f"/api/queries/{query_id}/results")
    return await handle_query_result_response(raw)
