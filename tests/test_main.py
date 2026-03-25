from redash_mcp import __main__


def test_build_parser_defaults_stdio(monkeypatch):
    monkeypatch.delenv("REDASH_MCP_TRANSPORT", raising=False)
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)

    args = __main__.build_parser().parse_args([])

    assert args.transport == "stdio"


def test_build_parser_reads_transport_env(monkeypatch):
    monkeypatch.setenv("REDASH_MCP_TRANSPORT", "streamable-http")

    args = __main__.build_parser().parse_args([])

    assert args.transport == "streamable-http"


def test_build_parser_reads_legacy_transport_env(monkeypatch):
    monkeypatch.delenv("REDASH_MCP_TRANSPORT", raising=False)
    monkeypatch.setenv("MCP_TRANSPORT", "streamable-http")

    args = __main__.build_parser().parse_args([])

    assert args.transport == "streamable-http"


def test_main_runs_selected_transport(monkeypatch):
    call = {}

    def fake_runner():
        call["transport"] = "streamable-http"

    monkeypatch.setitem(__main__.TRANSPORT_RUNNERS, "streamable-http", fake_runner)

    __main__.main(["--transport", "streamable-http"])

    assert call == {"transport": "streamable-http"}
