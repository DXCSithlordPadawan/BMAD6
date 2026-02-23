# Containerfile — BMAD v6 Template Architect
# Compatible with Podman and Docker.
# Build:  podman build -t bmad6-architect .
# Run:    podman run -p 8000:8000 --env-file .env bmad6-architect

# ── Stage 1: dependency installation ─────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install dependencies into a separate prefix for clean copying
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.12-slim

# Security: run as a non-root user
RUN groupadd -r bmad && useradd -r -g bmad -d /app -s /sbin/nologin bmad

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY --chown=bmad:bmad app.py           ./app.py
COPY --chown=bmad:bmad config/          ./config/
COPY --chown=bmad:bmad templates/       ./templates/
COPY --chown=bmad:bmad static/          ./static/
COPY --chown=bmad:bmad agent/           ./agent/

# Create output directory with correct ownership
RUN mkdir -p /app/bmad_output && chown bmad:bmad /app/bmad_output

USER bmad

EXPOSE 8000

# Health check so orchestrators (Podman Play Kube / Kubernetes) can verify readiness
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# SECURITY: do not set a default SECRET_KEY here — always inject via --env-file or -e
ENV FLASK_APP=app.py \
    FLASK_DEBUG=0 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

CMD ["python", "app.py"]
