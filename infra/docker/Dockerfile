# syntax=docker/dockerfile:1.7

FROM rust:1.88-bookworm AS ucp-schema-builder

ARG UCP_SCHEMA_VERSION=1.3.0

RUN cargo install ucp-schema \
    --version "${UCP_SCHEMA_VERSION}" \
    --locked

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS docs-builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY --from=ucp-schema-builder /usr/local/cargo/bin/ucp-schema /usr/local/bin/ucp-schema

RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    fonts-noto-color-emoji \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    make \
    && rm -rf /var/lib/apt/lists/*

COPY . .

ARG SITE_URL

RUN SITE_URL="${SITE_URL}" make docs-build

FROM python:3.13-slim AS runtime

ENV PORT=8080 \
    PYTHONUNBUFFERED=1

WORKDIR /site

COPY --from=docs-builder /app/site /site

EXPOSE 8080
USER 10001:10001

CMD ["sh", "-c", "python -m http.server \"${PORT}\" --bind 0.0.0.0 --directory /site"]
