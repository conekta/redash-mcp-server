import json

from redash_mcp.client import redash_get
from redash_mcp.server import mcp


@mcp.tool()
async def list_query_visualizations(query_id: int) -> str:
    """List all visualizations for a query.

    Fetches the query and extracts its visualizations array.
    """
    result = await redash_get(f"/api/queries/{query_id}")
    try:
        data = json.loads(result)
    except json.JSONDecodeError:
        return result
    if "error" in data:
        return result
    visualizations = data.get("visualizations", [])
    return json.dumps(visualizations, indent=2, ensure_ascii=False)
