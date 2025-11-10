# Multi-stage build to reduce final image size

# Stage 1: Builder
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (no dev dependencies)
RUN uv sync --frozen --no-dev

# Stage 2: Runtime
FROM python:3.11-slim

# Install runtime system dependencies including Tectonic
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Tectonic from pre-built binaries (avoiding installer issues)
# Using latest release from GitHub
RUN TECTONIC_VERSION="0.15.0" \
    && ARCH="x86_64-unknown-linux-musl" \
    && echo "Installing Tectonic ${TECTONIC_VERSION} for ${ARCH}" \
    && curl -fsSL "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic@${TECTONIC_VERSION}/tectonic-${TECTONIC_VERSION}-${ARCH}.tar.gz" \
        -o /tmp/tectonic.tar.gz \
    && tar -xzf /tmp/tectonic.tar.gz -C /usr/local/bin/ \
    && chmod +x /usr/local/bin/tectonic \
    && rm /tmp/tectonic.tar.gz \
    && echo "Tectonic installed successfully" \
    && tectonic --version

# Install uv (lightweight)
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code only (not tests, examples, etc.)
COPY app ./app
COPY pyproject.toml uv.lock ./

# Pre-download FastEmbed model for semantic cache (if enabled)
# This avoids downloading on first request (saves 10-20s cold start time)
RUN echo "Pre-downloading FastEmbed model..." \
    && /app/.venv/bin/python -c "from fastembed import TextEmbedding; TextEmbedding('BAAI/bge-small-en-v1.5')" \
    && echo "FastEmbed model cached successfully"

# Create directories for LaTeX compilation
RUN mkdir -p /tmp/latex-editor-project /tmp/latex-editor-output

# Expose port
EXPOSE 8000

# Run the application
CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
