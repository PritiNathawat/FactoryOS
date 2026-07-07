# ============================================================
# FactoryOS — Backend Dockerfile
#
# Multi-stage build:
#   Stage 1 (builder): Install Python dependencies (may require gcc/build tools)
#   Stage 2 (runtime): Lean production image — no build tools, non-root user
# ============================================================

# ──────────────────────────────────────────────────────────────
# Stage 1: Builder
# Install all Python dependencies into an isolated prefix.
# This stage is discarded from the final image.
# ──────────────────────────────────────────────────────────────
# Python 3.11: matches the development virtual environment.
# All packages in requirements.txt have pre-built wheels for cp311 — no compilation needed.
FROM python:3.11-slim AS builder

WORKDIR /build

# No system build tools needed — all deps ship as pre-built wheels for Python 3.11.
# Upgrade pip first — old pip versions can silently install wrong package versions.
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install \
        --no-cache-dir \
        --prefix=/install \
        -r requirements.txt


# ──────────────────────────────────────────────────────────────
# Stage 2: Runtime
# Minimal, secure production image. Nothing from Stage 1 except
# the compiled Python packages.
# ──────────────────────────────────────────────────────────────
# Python 3.11 runtime — matches builder stage exactly.
FROM python:3.11-slim AS runtime

# No additional system libraries needed — SQLite is bundled in the Python image.
# If switching to PostgreSQL, add libpq5 here and install requirements-prod.txt in builder.

# Security: create a dedicated non-root user and group.
# The UID/GID 1001 avoids collision with common system users.
RUN groupadd --gid 1001 factoryos \
    && useradd \
        --uid 1001 \
        --gid factoryos \
        --shell /bin/false \
        --no-create-home \
        factoryos

WORKDIR /app

# Copy compiled packages from the builder stage.
COPY --from=builder /install /usr/local

# Copy application source code.
COPY app/ ./app/

# Transfer ownership to the non-root user before switching context.
RUN chown -R factoryos:factoryos /app

# All subsequent commands and the final CMD run as non-root.
USER factoryos

# Python runtime best practices:
#   PYTHONDONTWRITEBYTECODE — do not write .pyc files into the image layer
#   PYTHONUNBUFFERED        — flush stdout/stderr immediately (critical for container logs)
#   PYTHONPATH              — ensures `app` is importable as a top-level package
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

EXPOSE 8000

# Health check: uses Python's stdlib urllib — no extra tooling needed in the image.
# Cloud Run, Kubernetes, and Docker Compose use this to decide if the container is ready.
HEALTHCHECK \
    --interval=30s \
    --timeout=10s \
    --start-period=15s \
    --retries=3 \
    CMD python -c \
        "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"

# Start the Uvicorn ASGI server in production mode.
# --host 0.0.0.0 binds to all interfaces inside the container.
# For development hot-reload, docker-compose overrides this CMD.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
