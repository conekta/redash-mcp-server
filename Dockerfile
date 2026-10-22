FROM python:3.13-slim AS base

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# emSign (CA comprometida, 20-oct-2026): pip>=26.2.2 trae su certifi vendorizado sin la
# raíz «emSign ECC Root CA - G3». Fija el piso: python:3.11/3.12-slim todavía traen
# pip 24.0/25.0.1 (medido 22-oct-2026); 3.13/3.14 ya traen 26.2.2.
RUN pip install --no-cache-dir --upgrade "pip>=26.2.2"

COPY pyproject.toml .
RUN uv sync --extra dev --no-install-project

COPY src/ src/
COPY tests/ tests/
RUN uv sync --extra dev

EXPOSE 8000

CMD ["uv", "run", "python", "-m", "redash_mcp"]
