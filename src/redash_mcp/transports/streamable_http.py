from redash_mcp.auth import get_request_header_api_key, set_api_key_provider
from redash_mcp.server import mcp
from redash_mcp.tools import initialize


def run() -> None:
    initialize()
    set_api_key_provider(get_request_header_api_key)
    mcp.run(transport="streamable-http")
