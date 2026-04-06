# Redash MCP Server

MCP server that exposes the Redash API as tools for Claude.

## Quick Start

```bash
uv sync --extra dev          # Install dependencies
cp .env.example .env         # Configure environment variables
uv run python -m redash_mcp  # Start server (stdio)
```

## Project Structure

```
src/redash_mcp/
├── auth.py          # API key provider (strategy pattern)
├── client.py        # Singleton httpx client for Redash API
├── jobs.py          # Async job polling helpers (poll_job, handle_query_result_response)
├── server.py        # FastMCP server instance + /ping health check
├── __main__.py      # CLI entrypoint with transport selection
├── transports/      # stdio and streamable-http transport runners
└── tools/           # One module per Redash resource
    ├── queries.py         # list, get, create, update, search, recent, archive, refresh
    ├── dashboards.py      # list, get, create, update
    ├── data_sources.py    # list, get, schema, test connection
    ├── query_results.py   # get results, execute query, execute sql
    ├── users.py           # list, get
    ├── alerts.py          # list, get, create
    └── visualizations.py  # list visualizations for a query
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `REDASH_API_KEY` | Yes | Redash API key (found in user profile) |
| `REDASH_URL` | Yes | Redash instance URL (e.g. `https://redash.data.conekta.io`) |
| `REDASH_MCP_TRANSPORT` | No | Transport mode: `stdio` (default) or `streamable-http` |
| `REDASH_MCP_HOST` | No | HTTP host (default: `127.0.0.1`) |
| `REDASH_MCP_PORT` | No | HTTP port (default: `8000`) |

## Auth

Redash uses `Authorization: Key <api_key>` header (not Bearer). The auth module follows a strategy pattern:
- **stdio**: reads `REDASH_API_KEY` from environment
- **streamable-http**: reads API key from `Authorization` request header

## Running Tests

```bash
uv run pytest tests/ -v
uv run pytest tests/ --cov=redash_mcp --cov-report=term-missing
```

## Docker

```bash
docker build -t redash-mcp .
docker run -i --rm -e REDASH_API_KEY -e REDASH_URL redash-mcp
```

## Claude Desktop Config

```json
{
  "mcpServers": {
    "redash": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "REDASH_API_KEY", "-e", "REDASH_URL", "redash-mcp"],
      "env": {
        "REDASH_API_KEY": "<your-api-key>",
        "REDASH_URL": "https://your-redash-instance.com"
      }
    }
  }
}
```

## Conventions

- Tools use `redash_get()` / `redash_request()` from `client.py` — never call httpx directly
- JSON parameters in tools are passed as string (`parameters_json`) and parsed inside
- All tools are async and registered via `@mcp.tool()` decorator
- Tests use `respx` to mock HTTP calls to Redash API
