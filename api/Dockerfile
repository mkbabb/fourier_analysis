FROM python:3.13-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

FROM ghcr.io/astral-sh/uv:latest AS uv

FROM base AS deps
COPY --from=uv /uv /usr/local/bin/
COPY pyproject.toml uv.lock ./
COPY src/ src/
RUN uv sync --frozen --no-dev --extra web

FROM deps AS development
RUN uv sync --frozen --extra web --extra dev
COPY . .
CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM deps AS production
RUN adduser --disabled-password app
COPY . .
RUN chown -R app:app /app/.venv
ENV UV_CACHE_DIR=/tmp/uv-cache
USER app
CMD ["uv", "run", "--no-sync", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--proxy-headers", "--forwarded-allow-ips", "*"]
