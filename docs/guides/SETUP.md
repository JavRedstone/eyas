# Setup & Development

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

pip install -r eyas/requirements.txt
python eyas/app.py
# Open http://localhost:7860
```

Korean UI:

```bash
python eyas/app.py --lang ko
```

---

## Video filename convention

Eyas reads the **zone** and **recording time** from the filename. Use this pattern when naming clips before uploading:

```
YYYYMMDD_HHMMSS_<zone>.<ext>
```

Supported formats: `.mp4`, `.m4v` (and any format readable by OpenCV).

| Part | Format | Example |
|---|---|---|
| Date | 8-digit `YYYYMMDD` | `20260615` |
| Time | 6-digit `HHMMSS` | `130000` |
| Zone | any string (underscores allowed) | `entrance`, `counter`, `aisle1` |

**Examples**

```
20260615_130000_aisle1.m4v  → zone "aisle1", recorded 2026-06-15 at 13:00
20260608_120000_entrance.mp4 → zone "entrance"
```

If the filename does not match this pattern the pipeline falls back to a generic `review_area` zone that covers the full frame.

**Bundled sample clips**

| File | Zone | Source |
|---|---|---|
| `20260615_130000_aisle1.m4v` | `aisle1` | Joy Convenience Store |
| `20260615_130000_aisle2.m4v` | `aisle2` | Joy Convenience Store |
| `20260615_130000_aisle3.m4v` | `aisle3` | Joy Convenience Store |
| `20260615_130000_aisle4.m4v` | `aisle4` | Joy Convenience Store |
| `20260608_120000_entrance.mp4` | `entrance` | Online footage |
| `20260608_130000_counter.mp4` | `counter` | Online footage |

---

## Build workflows

### 1 — Local development (hot reload)

```bash
# Terminal 1 — Gradio backend
python eyas/app.py               # http://localhost:7860

# Terminal 2 — React dev server (hot reload)
(cd eyas/ui/frontend && npm install)
(cd eyas/ui/frontend && npm run dev)    # http://localhost:5173
```

Open `http://localhost:5173`. The frontend connects to the Gradio backend at `http://127.0.0.1:7860`, so both servers must be running.

To use a different backend port:

```bash
python eyas/app.py --port 7861
(cd eyas/ui/frontend && VITE_GRADIO_BACKEND_URL=http://127.0.0.1:7861 npm run dev)
```

### 2 — Production build (static files)

Vite compiles the SPA into `eyas/ui/dist/`. Gradio serves those files as static assets — no separate Node process needed at runtime.

```bash
(cd eyas/ui/frontend && npm run build)    # → eyas/ui/dist/
python eyas/app.py
# Open http://localhost:7860
```

### 3 — Docker

The [Dockerfile](Dockerfile) runs the frontend build and model pre-download as part of `docker build`, producing a self-contained image.

```bash
docker build -t eyas .
docker run -p 7860:7860 eyas
# Open http://localhost:7860
```

Pass a Hugging Face token for gated models:

```bash
docker build --build-arg HF_TOKEN=hf_xxx -t eyas .
```

**Build order inside Docker:**
1. System deps — libgl, Node 20, git-lfs
2. `npm ci` (package.json copied first for layer caching)
3. `npm run build` → `eyas/ui/dist/`
4. `llama-cpp-python` from pre-built CPU wheels (no C++ compilation)
5. Python deps from `requirements.txt`
6. App code
7. `download_models.py` — bakes YOLO and GGUF models into the image

---

## Repository layout

```
eyas/
  app.py                  Entry point — loads prefs and launches Gradio
  model_registry.py       Lazy model loader
  visual_pipeline.py      Main pipeline orchestrator
  object_detection/       YOLO11n + BotSORT tracker
  video_processing/       MiniCPM-V VLM wrapper
  event_structuring/      Heuristic event builder
  llm/                    Nemotron reasoner (llama.cpp)
  postprocessing/         Translation (TinyAya) + TTS (VoxCPM2)
  storage/                Clip index
  ui/                     Gradio API + React frontend
    frontend/             React + Vite + MUI source
    dist/                 Built SPA (committed, served by Gradio)
  utils/                  Shared helpers
  scripts/                CLI entry points
  models/                 Local weights (gitignored — auto-downloaded)
  input/                  Sample input videos
docs/                     Design and architecture notes
Dockerfile                HF Spaces / Docker deployment
scripts/download_models.py  Model pre-download for Docker build
```

---

## Pushing changes

### GitHub

```bash
git push origin main
```

### Hugging Face Spaces

HF Spaces has a 1 GB LFS storage limit. Always use an orphan commit to avoid pushing the full git history:

```bash
git checkout --orphan hf-deploy
git commit -m "Deploy to HF Spaces"
git push space hf-deploy:main --force
git checkout main
git branch -D hf-deploy
```

Or as a one-liner:

```bash
git checkout --orphan hf-deploy && git commit -m "Deploy to HF Spaces" && git push space hf-deploy:main --force && git checkout main && git branch -D hf-deploy
```

For ZeroGPU: switch the Space hardware to ZeroGPU in HF settings and add `EYAS_ZERO_GPU=1` as a Space variable.

> Sample videos in `eyas/input/` are committed directly (no LFS) so they ship with the HF build.
