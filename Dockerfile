FROM python:3.12-slim

# System deps: git-lfs, Node 20, and OpenCV runtime libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    git \
    git-lfs \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies (installed as root → /usr/local/lib, accessible to all
#    processes including ZeroGPU worker forks) ─────────────────────────────────
COPY eyas/requirements.txt /tmp/requirements.txt

# Try CUDA 12.4 wheel first; fall back to CPU wheel if unavailable at build time.
# ZeroGPU attaches the GPU at runtime, not during build, so CPU install is fine —
# llama-cpp-python will still find CUDA at inference time via the ZeroGPU bind-mount.
RUN pip install --no-cache-dir llama-cpp-python \
        --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124 \
    || pip install --no-cache-dir llama-cpp-python

RUN pip install --no-cache-dir -r /tmp/requirements.txt

# HF Spaces requires a non-root user
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH="/home/user/.local/bin:$PATH" \
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SERVER_PORT=7860

WORKDIR /app

# ── Frontend build ────────────────────────────────────────────────────────────
COPY --chown=user:user eyas/ui/frontend/package*.json ./eyas/ui/frontend/
RUN cd eyas/ui/frontend && npm ci

COPY --chown=user:user eyas/ui/frontend/ ./eyas/ui/frontend/
RUN cd eyas/ui/frontend && npm run build

# ── Application code ──────────────────────────────────────────────────────────
COPY --chown=user:user . .

# ── Pre-download models at build time ─────────────────────────────────────────
ARG HF_TOKEN=""
ENV HF_TOKEN=${HF_TOKEN}
RUN python3 scripts/download_models.py

WORKDIR /app/eyas

EXPOSE 7860

CMD ["python", "app.py"]
