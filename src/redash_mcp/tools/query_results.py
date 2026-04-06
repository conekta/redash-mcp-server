import asyncio
import json

from redash_mcp.client import redash_get, redash_request
from redash_mcp.server import mcp


async def _poll_job(job_id: str) -> str:
    # Redash job statuses: 1=pending, 2=started, 3=success, 4=error, 5=cancelled
    for _ in range(60):
        job_raw = await redash_get(f"/api/jobs/{job_id}")
        job_data = json.loads(job_raw)
        if job_data.get("error") is True:
            return job_raw
        job = job_data.get("job", {})
        status = job.get("status")
        if status in (4, 5):
            return json.dumps({"error": True, "message": job.get("error", "Query failed or cancelled")})
        if status == 3:
            result_id = job.get("query_result_id")
            if result_id is None:
                return json.dumps({"error": True, "message": "Missing query_result_id in job response"})
            return await redash_get(f"/api/query_results/{result_id}")
        await asyncio.sleep(1)
    return json.dumps({"error": True, "message": "Timed out waiting for query result"})


async def _handle_query_result_response(raw: str) -> str:
    data = json.loads(raw)
    if data.get("error") is True:
        return raw
    job = data.get("job")
    if job:
        return await _poll_job(job["id"])
    return raw


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
    return await _handle_query_result_response(raw)


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
    body: dict = {"query_id": query_id}
    if parameters_json is not None:
        try:
            body["parameters"] = json.loads(parameters_json)
        except json.JSONDecodeError:
            return json.dumps({"error": True, "message": "Invalid parameters_json"})

    raw = await redash_request("POST", "/api/query_results", body=body)
    return await _handle_query_result_response(raw)
