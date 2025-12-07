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

# Copy requirements and install with pip (more reliable than uv)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Verify uvicorn is installed
RUN which uvicorn && uvicorn --version

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.13-slim as runtime

WORKDIR /app

# Install runtime dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r graphrag && useradd -r -g graphrag graphrag

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn

# Set environment variables
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

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Run the application
CMD ["sh", "-c", "uvicorn biomedical_graphrag.application.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

