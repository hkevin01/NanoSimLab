# Multi-stage Dockerfile for NanoSimLab API
# Optimized for both development and production use

# Build stage
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILDKIT_INLINE_CACHE=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install wheel
RUN pip install --upgrade pip wheel setuptools

# Copy requirements first for better layer caching
COPY pyproject.toml /tmp/
WORKDIR /tmp

# Install Python dependencies
RUN pip install -e ".[analysis,dev]"

# Production stage
FROM python:3.11-slim as production

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    libopenblas0 \
    liblapack3 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create app user for security
RUN useradd --create-home --shell /bin/bash app
USER app

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=app:app src/ ./src/
COPY --chown=app:app pyproject.toml ./
COPY --chown=app:app README.md ./
COPY --chown=app:app LICENSE ./

# Install the package in development mode
RUN pip install -e .

# Create data directory for persistent storage
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONPATH="/app:$PYTHONPATH" \
    HOST=0.0.0.0 \
    PORT=8080 \
    WORKERS=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:$PORT/status || exit 1

# Expose port
EXPOSE 8080

# Default command - can be overridden
CMD ["python", "-m", "uvicorn", "nanosimlab.api:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]

# Development stage (for development mode)
FROM production as development

# Switch back to root for development tools
USER root

# Install development dependencies
RUN apt-get update && apt-get install -y \
    git \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Install additional Python development tools
RUN pip install \
    jupyter \
    ipython \
    debugpy

# Switch back to app user
USER app

# Enable hot reloading in development
CMD ["python", "-m", "uvicorn", "nanosimlab.api:app", "--host", "0.0.0.0", "--port", "8080", "--reload", "--reload-dir", "/app/src"]
