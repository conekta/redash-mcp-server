FROM python:3.13-slim AS base

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml .
RUN uv sync --extra dev --no-install-project

COPY src/ src/
COPY tests/ tests/
RUN uv sync --extra dev

EXPOSE 8000

CMD ["uv", "run", "python", "-m", "redash_mcp"]
