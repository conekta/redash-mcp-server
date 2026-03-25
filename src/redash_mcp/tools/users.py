from redash_mcp.client import build_params, redash_get
from redash_mcp.server import mcp


@mcp.tool()
async def list_users(page: int = 1, page_size: int = 25) -> str:
    """List all users with pagination."""
    params = build_params(page=page, page_size=page_size)
    return await redash_get("/api/users", params=params)


@mcp.tool()
async def get_user(user_id: int) -> str:
    """Get a specific user by their ID."""
    return await redash_get(f"/api/users/{user_id}")
