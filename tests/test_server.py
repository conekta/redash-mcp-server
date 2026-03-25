import importlib

from starlette.testclient import TestClient

from redash_mcp import server


def test_ping_healthcheck():
    client = TestClient(server.mcp.streamable_http_app())

    response = client.get("/ping")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_server_reads_http_settings_from_env(monkeypatch):
    monkeypatch.setenv("REDASH_MCP_HOST", "0.0.0.0")
    monkeypatch.setenv("REDASH_MCP_PORT", "9000")
    monkeypatch.setenv("REDASH_MCP_STREAMABLE_HTTP_PATH", "mcp-alt")

    reloaded_server = importlib.reload(server)

    assert reloaded_server.mcp.settings.host == "0.0.0.0"
    assert reloaded_server.mcp.settings.port == 9000
    assert reloaded_server.mcp.settings.streamable_http_path == "/mcp-alt"

    monkeypatch.delenv("REDASH_MCP_HOST", raising=False)
    monkeypatch.delenv("REDASH_MCP_PORT", raising=False)
    monkeypatch.delenv("REDASH_MCP_STREAMABLE_HTTP_PATH", raising=False)
    importlib.reload(reloaded_server)
