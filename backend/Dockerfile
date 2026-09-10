# ============================================
# Multi Job Portal Automation Tool - Backend
# Dockerfile
# ============================================

# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /usr/src/app/wheels -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder
COPY --from=builder /usr/src/app/wheels /usr/src/app/wheels
RUN pip install --no-cache-dir /usr/src/app/wheels/*.whl

# Remove wheels to save space
RUN rm -rf /usr/src/app/wheels

# Create non-root user
RUN groupadd -r celery && useradd -r -g celery -d /app -s /sbin/nologin celery

# Create necessary directories
RUN mkdir -p /app/logs /app/celery && \
    chown -R celery:celery /app

# Copy application code
COPY . .

# Set ownership
RUN chown -R celery:celery /app

# Switch to non-root user
USER celery

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
