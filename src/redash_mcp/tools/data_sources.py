from redash_mcp.client import build_params, redash_get, redash_request
from redash_mcp.server import mcp


@mcp.tool()
async def list_data_sources() -> str:
    """List all available data sources."""
    return await redash_get("/api/data_sources")


@mcp.tool()
async def get_data_source(data_source_id: int) -> str:
    """Get a specific data source by its ID."""
    return await redash_get(f"/api/data_sources/{data_source_id}")


@mcp.tool()
async def get_data_source_schema(
    data_source_id: int,
    refresh: bool = False,
) -> str:
    """Get the schema of a data source (tables and columns).

    Args:
        data_source_id: ID of the data source.
        refresh: If true, refresh the schema from the data source.
    """
    params = build_params(refresh="true" if refresh else None)
    return await redash_get(
        f"/api/data_sources/{data_source_id}/schema", params=params or None
    )


@mcp.tool()
async def check_data_source_connection(data_source_id: int) -> str:
    """Test the connection to a data source."""
    return await redash_request("POST", f"/api/data_sources/{data_source_id}/test")
