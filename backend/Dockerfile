FROM python:3.12

ENV PYTHONUNBUFFERED=1

WORKDIR /backend/

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.8.23 /uv /uvx /bin/

ENV PATH="/backend/.venv/bin:$PATH"

ENV UV_COMPILE_BYTECODE=1

ENV UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

ENV PYTHONPATH=/backend

COPY / /backend

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync

RUN chmod +x entrypoint.sh

ENTRYPOINT ["/backend/entrypoint.sh"]