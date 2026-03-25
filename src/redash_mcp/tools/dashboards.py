import json

from redash_mcp.client import build_params, redash_get, redash_request
from redash_mcp.server import mcp


@mcp.tool()
async def list_dashboards(
    page: int = 1,
    page_size: int = 25,
    search: str | None = None,
) -> str:
    """List dashboards with optional search and pagination."""
    params = build_params(page=page, page_size=page_size, q=search)
    return await redash_get("/api/dashboards", params=params)


@mcp.tool()
async def get_dashboard(dashboard_id_or_slug: str) -> str:
    """Get a specific dashboard by its ID or slug."""
    return await redash_get(f"/api/dashboards/{dashboard_id_or_slug}")


@mcp.tool()
async def create_dashboard(name: str) -> str:
    """Create a new dashboard."""
    return await redash_request("POST", "/api/dashboards", body={"name": name})


@mcp.tool()
async def update_dashboard(
    dashboard_id: int,
    name: str | None = None,
    is_draft: bool | None = None,
    tags_json: str | None = None,
) -> str:
    """Update an existing dashboard.

    Args:
        dashboard_id: ID of the dashboard to update.
        name: New name for the dashboard.
        is_draft: Whether the dashboard is a draft.
        tags_json: Optional JSON string with list of tags, e.g. '["tag1", "tag2"]'.
    """
    body = build_params(name=name, is_draft=is_draft)
    if tags_json is not None:
        try:
            body["tags"] = json.loads(tags_json)
        except json.JSONDecodeError:
            return json.dumps({"error": True, "message": "Invalid tags_json"})
    if not body:
        return json.dumps({"error": True, "message": "No fields to update."})
    return await redash_request("POST", f"/api/dashboards/{dashboard_id}", body=body)
