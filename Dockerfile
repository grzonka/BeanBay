# Stage 1: Build wheel (hatch_build.py builds the frontend automatically)
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

ARG SETUPTOOLS_SCM_PRETEND_VERSION
ENV SETUPTOOLS_SCM_PRETEND_VERSION=${SETUPTOOLS_SCM_PRETEND_VERSION}

RUN apt update && \
    apt install -y --no-install-recommends git curl unzip && \
    curl -fsSL https://bun.sh/install | bash && \
    rm -rf /var/lib/apt/lists/*
ENV PATH="/root/.bun/bin:$PATH"

WORKDIR /build
COPY . /src
RUN --mount=type=cache,target=/root/.cache/uv \
    cd /src && uv build --wheel --out-dir /build/dist

# Stage 2: Runtime (CPU-only torch via extra index to avoid ~2GB CUDA wheel)
FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY --from=builder /build/dist/*.whl /tmp/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    /tmp/*.whl && rm /tmp/*.whl

ENV BEANBAY_DATABASE_URL=sqlite:////data/beanbay.db
ENV PYTHONUNBUFFERED=1

RUN mkdir -p /data

EXPOSE 8000
CMD ["beanbay"]
