# Redash MCP Server

MCP server for the [Redash](https://redash.io) API. Exposes Redash's core data operations as tools for the [Model Context Protocol](https://modelcontextprotocol.io).

## Setup

```bash
# Install dependencies
uv sync

# Set your Redash API key and URL
export REDASH_API_KEY=your_api_key
export REDASH_URL=https://redash.example.com

# Run the server
uv run python -m redash_mcp
```

By default the server uses the `stdio` transport for local MCP clients such as Claude Desktop.

## Hosted MCP

The server can be deployed as a remote MCP endpoint over Streamable HTTP:

```bash
uv run python -m redash_mcp --transport streamable-http
```

Send your Redash API key in the request header:

```text
Authorization: Key your_api_key
```

### Configuration (Hosted / Streamable HTTP)

If your MCP client supports remote servers over HTTP, the JSON config should include the hosted URL and the `Authorization` header.

Example:

```json
{
  "mcpServers": {
    "redash": {
      "url": "https://your-mcp-host.com/mcp",
      "headers": {
        "Authorization": "Key your_api_key"
      }
    }
  }
}
```

Notes:

- Replace `your_api_key` with your real Redash API key.
- The header must be exactly `Authorization`.
- The value must include the `Key ` prefix.

### Claude Code (CLI)

```bash
claude mcp add --transport http redash https://your-mcp-host.com/mcp \
  --header "Authorization: Key your_api_key"
```

Replace `your_api_key` with your real Redash API key.

## Configuration (Claude Desktop / stdio)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "redash": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/redash-mcp-server", "run", "python", "-m", "redash_mcp"],
      "env": {
        "REDASH_API_KEY": "your_api_key",
        "REDASH_URL": "https://redash.example.com"
      }
    }
  }
}
```

## Available Tools

| Resource | Tools |
|----------|-------|
| Queries | `list_queries`, `get_query`, `create_query`, `update_query`, `search_queries`, `get_recent_queries`, `archive_query`, `refresh_query` |
| Dashboards | `list_dashboards`, `get_dashboard`, `create_dashboard`, `update_dashboard` |
| Data Sources | `list_data_sources`, `get_data_source`, `get_data_source_schema`, `check_data_source_connection` |
| Query Results | `get_query_result`, `execute_query` |
| Users | `list_users`, `get_user` |
| Alerts | `list_alerts`, `get_alert`, `create_alert` |
| Visualizations | `list_query_visualizations` |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REDASH_API_KEY` | Redash API key (required for stdio transport) | — |
| `REDASH_URL` | Base URL of your Redash instance | `http://localhost:5000` |
| `REDASH_MCP_TRANSPORT` | Transport type (`stdio` or `streamable-http`) | `stdio` |
| `REDASH_MCP_HOST` | Host to bind HTTP server | `127.0.0.1` |
| `REDASH_MCP_PORT` | Port for HTTP server | `8000` |
| `REDASH_MCP_STREAMABLE_HTTP_PATH` | HTTP path for MCP endpoint | `/mcp` |

## Docker

```bash
# Build the image
docker build -t redash-mcp .

docker run -i --rm \
  -e REDASH_API_KEY=your_api_key \
  -e REDASH_URL=https://redash.example.com \
  redash-mcp
```

### Configuration (Claude Desktop with Docker / stdio)

```json
{
  "mcpServers": {
    "redash": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "REDASH_API_KEY", "-e", "REDASH_URL", "redash-mcp"],
      "env": {
        "REDASH_API_KEY": "your_api_key",
        "REDASH_URL": "https://redash.example.com"
      }
    }
  }
}
```

## Development

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests
uv run pytest tests/ -v
```
