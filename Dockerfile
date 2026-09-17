FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.13 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

RUN chmod +x docker/entrypoint.sh

RUN groupadd -r app && useradd -r -g app app && chown -R app:app /app
USER app

ENTRYPOINT ["docker/entrypoint.sh"]
