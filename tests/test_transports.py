from redash_mcp import auth
from redash_mcp.transports import TRANSPORT_RUNNERS
from redash_mcp.transports import stdio, streamable_http


def test_transport_runners_register_known_transports():
    assert TRANSPORT_RUNNERS == {
        "stdio": stdio.run,
        "streamable-http": streamable_http.run,
    }


def test_stdio_run_sets_env_provider_and_uses_stdio_transport(monkeypatch):
    calls = {}

    def fake_initialize():
        calls["initialized"] = True

    def fake_set_api_key_provider(provider):
        calls["provider"] = provider

    def fake_run(*, transport):
        calls["transport"] = transport

    monkeypatch.setattr(stdio, "initialize", fake_initialize)
    monkeypatch.setattr(stdio, "set_api_key_provider", fake_set_api_key_provider)
    monkeypatch.setattr(stdio.mcp, "run", fake_run)

    stdio.run()

    assert calls == {
        "initialized": True,
        "provider": auth.get_env_api_key,
        "transport": "stdio",
    }


def test_streamable_http_run_sets_header_provider_and_uses_transport(monkeypatch):
    calls = {}

    def fake_initialize():
        calls["initialized"] = True

    def fake_set_api_key_provider(provider):
        calls["provider"] = provider

    def fake_run(*, transport):
        calls["transport"] = transport

    monkeypatch.setattr(streamable_http, "initialize", fake_initialize)
    monkeypatch.setattr(
        streamable_http, "set_api_key_provider", fake_set_api_key_provider
    )
    monkeypatch.setattr(streamable_http.mcp, "run", fake_run)

    streamable_http.run()

    assert calls == {
        "initialized": True,
        "provider": auth.get_request_header_api_key,
        "transport": "streamable-http",
    }
