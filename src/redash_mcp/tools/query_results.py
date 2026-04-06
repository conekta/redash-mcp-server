import json

from redash_mcp.client import redash_get, redash_request
from redash_mcp.server import mcp
from redash_mcp.jobs import handle_query_result_response


@mcp.tool()
async def execute_sql(data_source_id: int, query: str, max_age: int = 0) -> str:
    """Execute SQL directly against a data source without saving a query.

    Blocks until results are ready (up to 60 seconds for async jobs).

    Args:
        data_source_id: ID of the data source to run the query against.
        query: SQL query string to execute.
        max_age: Use cached result if younger than this many seconds (0 = always re-run).
    """
    raw = await redash_request(
        "POST", "/api/query_results",
        body={"data_source_id": data_source_id, "query": query, "max_age": max_age},
    )
    return await handle_query_result_response(raw)


@mcp.tool()
async def get_query_result(query_id: int) -> str:
    """Get the latest result for a query."""
    return await redash_get(f"/api/queries/{query_id}/results")


@mcp.tool()
async def execute_query(
    query_id: int,
    parameters_json: str | None = None,
) -> str:
    """Execute a saved query and return the result.

    Args:
        query_id: ID of the saved query to execute.
        parameters_json: Optional JSON string with query parameters,
            e.g. '{"date": "2024-01-01"}'.
    """
    body: dict = {}
    if parameters_json is not None:
        try:
            body["parameters"] = json.loads(parameters_json)
        except json.JSONDecodeError:
            return json.dumps({"error": True, "message": "Invalid parameters_json"})

    raw = await redash_request("POST", f"/api/queries/{query_id}/results", body=body)
    return await handle_query_result_response(raw)
