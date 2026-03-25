import json

from redash_mcp.client import redash_get, redash_request
from redash_mcp.server import mcp


@mcp.tool()
async def get_query_result(query_id: int) -> str:
    """Get the latest result for a query."""
    return await redash_get(f"/api/queries/{query_id}/results")


@mcp.tool()
async def execute_query(
    query_id: int,
    parameters_json: str | None = None,
) -> str:
    """Execute a query and return the result or job status.

    Args:
        query_id: ID of the query to execute.
        parameters_json: Optional JSON string with query parameters,
            e.g. '{"date": "2024-01-01"}'.
    """
    body: dict = {"query_id": query_id}
    if parameters_json is not None:
        try:
            body["parameters"] = json.loads(parameters_json)
        except json.JSONDecodeError:
            return json.dumps({"error": True, "message": "Invalid parameters_json"})
    return await redash_request("POST", "/api/query_results", body=body)
