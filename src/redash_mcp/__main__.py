from __future__ import annotations

import argparse
import os

from redash_mcp.transports import TRANSPORT_RUNNERS


def _get_env(*names: str, default: str | None = None) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value is not None:
            return value
    return default


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Redash MCP server over stdio or Streamable HTTP."
    )
    parser.add_argument(
        "--transport",
        choices=tuple(TRANSPORT_RUNNERS),
        default=_get_env("REDASH_MCP_TRANSPORT", "MCP_TRANSPORT", default="stdio"),
        help="Transport to expose. Defaults to stdio.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    TRANSPORT_RUNNERS[args.transport]()


if __name__ == "__main__":  # pragma: no cover
    main()
