FROM python:3.11-slim

# Copy Docker CLI binary from the official image (ARM64-compatible)
COPY --from=docker:27-cli /usr/local/bin/docker /usr/local/bin/docker

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app/ ./app/

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
