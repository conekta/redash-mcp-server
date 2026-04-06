import asyncio
import json

from redash_mcp.client import redash_get


async def poll_job(job_id: str) -> str:
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


async def handle_query_result_response(raw: str) -> str:
    data = json.loads(raw)
    if data.get("error") is True:
        return raw
    job = data.get("job")
    if job:
        return await poll_job(job["id"])
    return raw
