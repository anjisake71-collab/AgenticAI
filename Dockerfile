# ─── Dockerfile ──────────────────────────────────────────────────────────────
# Multi-stage build — lean production image (~200 MB)
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: builder ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --prefix=/install --no-cache-dir -r requirements.txt


# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Non-root user for security
RUN useradd -m -u 1000 agent
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY --chown=agent:agent . .

# Create runtime directories
RUN mkdir -p logs workspace memory/store \
 && chown -R agent:agent logs workspace memory

USER agent

# ── Health check ──────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import anthropic; print('ok')" || exit 1

# ── Default command ───────────────────────────────────────────────────────────
# Override with: docker run ... python run_react_agent.py --task "..."
CMD ["python", "run_react_agent.py", "--demo", "0"]
