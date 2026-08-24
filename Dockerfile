# =============================================================================
# Stage 1 — builder
# Installs build tools, builds the wheel, then installs all runtime deps into
# /install so Stage 2 can copy only the compiled site-packages.
# =============================================================================
FROM python:3.12-slim AS builder

# System build deps (needed by some compiled packages; remove if not required)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy only the packaging metadata first (better layer caching)
COPY pyproject.toml README.md ./

# Copy source so hatchling can build the wheel
COPY src/ ./src/

# Upgrade pip + install build frontend
RUN pip install --upgrade pip hatchling

# Build the wheel into /build/dist/
RUN pip wheel --no-deps --wheel-dir /build/dist .

# Install the wheel plus all runtime dependencies into an isolated prefix
RUN pip install \
        --prefix=/install \
        --no-deps \
        /build/dist/*.whl \
    && pip install \
        --prefix=/install \
        "sqlalchemy>=2.0" \
        "fastapi>=0.111" \
        "uvicorn[standard]>=0.29" \
        "pydantic>=2.0"


# =============================================================================
# Stage 2 — runtime
# Minimal image: no compiler, no dev tools, no test dependencies.
# =============================================================================
FROM python:3.12-slim AS runtime

# Non-root user for security
RUN groupadd --gid 1001 appgroup \
 && useradd  --uid 1001 --gid appgroup --no-create-home appuser

# Copy compiled packages from builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Copy application source (already installed as a package, but keep it for
# direct imports and to avoid editable-install complexity in production)
COPY src/ ./src/

# Environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Override in Kubernetes / docker-compose:
    DATABASE_URL="" \
    NOTIFICATION_WEBHOOK_URL="https://notifications.example.com/webhooks/orders" \
    PORT=8000

USER appuser

EXPOSE ${PORT}

# Healthcheck — matches the /health endpoint in app.py
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')"

# Uvicorn with a single worker by default; scale horizontally with replicas
CMD ["sh", "-c", \
     "uvicorn src.frameworks.http.fastapi.app:app \
      --host 0.0.0.0 \
      --port ${PORT} \
      --workers 1 \
      --log-level info"]
