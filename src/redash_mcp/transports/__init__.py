from collections.abc import Callable

from redash_mcp.transports.stdio import run as run_stdio
from redash_mcp.transports.streamable_http import run as run_streamable_http

TransportRunner = Callable[[], None]

TRANSPORT_RUNNERS: dict[str, TransportRunner] = {
    "stdio": run_stdio,
    "streamable-http": run_streamable_http,
}
