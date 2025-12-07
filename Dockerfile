# Biomedical GraphRAG - Production Dockerfile
# Multi-stage build for optimized image size

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.13-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster package installation
RUN pip install uv

# Copy dependency files and README (required by pyproject.toml)
COPY pyproject.toml ./
COPY uv.lock ./
COPY README.md ./

# Create virtual environment and install dependencies
RUN uv venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
RUN uv sync --frozen --no-dev

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.13-slim as runtime

WORKDIR /app

# Install runtime dependencies (curl for healthcheck, wget as backup)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r graphrag && useradd -r -g graphrag graphrag

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Set all environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"
ENV PYTHONUNBUFFERED=1

# Copy application code
COPY src/ ./src/
COPY frontend/ ./frontend/
COPY data/ ./data/

# Change ownership to non-root user
RUN chown -R graphrag:graphrag /app

# Switch to non-root user
USER graphrag

# Expose port (Railway sets PORT env var)
EXPOSE 8000

# Health check (uses default port, Railway handles port mapping)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Run the application (uses PORT env var if set, defaults to 8000)
CMD ["sh", "-c", "uvicorn biomedical_graphrag.application.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

