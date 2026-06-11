FROM python:3.12-slim

# System deps: OpenCV, build tools for llama-cpp-python, Node.js for frontend build
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    build-essential \
    cmake \
    git \
    git-lfs \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

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

# ── Python dependencies ───────────────────────────────────────────────────────
COPY --chown=user:user eyas/requirements.txt ./requirements.txt

# CPU-only llama-cpp-python (avoids CUDA toolchain requirement)
RUN CMAKE_ARGS="-DGGML_BLAS=OFF -DGGML_CUDA=OFF" pip install --no-cache-dir llama-cpp-python

RUN pip install --no-cache-dir -r requirements.txt

# ── Application code ──────────────────────────────────────────────────────────
COPY --chown=user:user . .

# ── Pre-download models at build time ─────────────────────────────────────────
# HF_TOKEN is passed from Space secrets as a build ARG
ARG HF_TOKEN=""
ENV HF_TOKEN=${HF_TOKEN}
RUN python3 scripts/download_models.py

WORKDIR /app/eyas

EXPOSE 7860

CMD ["python", "app.py"]
