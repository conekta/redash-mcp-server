import asyncio
import json

from redash_mcp.client import redash_get

_STATUS_SUCCESS = 3
_STATUS_ERROR = 4
_STATUS_CANCELLED = 5


def _error(message: str) -> str:
    return json.dumps({"error": True, "message": message}, indent=2, ensure_ascii=False)


async def poll_job(job_id: str) -> str:
    for _ in range(60):
        job_raw = await redash_get(f"/api/jobs/{job_id}")
        job_data = json.loads(job_raw)
        if job_data.get("error") is True:
            return job_raw
        job = job_data.get("job", {})
        status = job.get("status")
        if status in (_STATUS_ERROR, _STATUS_CANCELLED):
            return _error(job.get("error", "Query failed or cancelled"))
        if status == _STATUS_SUCCESS:
            result_id = job.get("query_result_id")
            if result_id is None:
                return _error("Missing query_result_id in job response")
            return await redash_get(f"/api/query_results/{result_id}")
        await asyncio.sleep(1)
    return _error("Timed out waiting for query result")


async def handle_query_result_response(raw: str) -> str:
    data = json.loads(raw)
    if data.get("error") is True:
        return raw
    job = data.get("job")
    if job:
        return await poll_job(job["id"])
    return raw
