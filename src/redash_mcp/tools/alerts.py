import json

from redash_mcp.client import redash_get, redash_request
from redash_mcp.server import mcp


@mcp.tool()
async def list_alerts() -> str:
    """List all alerts."""
    return await redash_get("/api/alerts")


@mcp.tool()
async def get_alert(alert_id: int) -> str:
    """Get a specific alert by its ID."""
    return await redash_get(f"/api/alerts/{alert_id}")


@mcp.tool()
async def create_alert(
    query_id: int,
    name: str,
    options_json: str,
) -> str:
    """Create a new alert for a query.

    Args:
        query_id: ID of the query to monitor.
        name: Name of the alert.
        options_json: JSON string with alert options,
            e.g. '{"column": "count", "op": "greater than", "value": 100}'.
    """
    try:
        options = json.loads(options_json)
    except json.JSONDecodeError:
        return json.dumps({"error": True, "message": "Invalid options_json"})
    body = {
        "query_id": query_id,
        "name": name,
        "options": options,
    }
    return await redash_request("POST", "/api/alerts", body=body)
