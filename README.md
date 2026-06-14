---
title: Eyas — AI Security Camera Agent
emoji: 🦅
colorFrom: blue
colorTo: yellow
pinned: false
sdk: gradio
sdk_version: 5.38.0
python_version: "3.12"
app_file: eyas/app.py
license: mit
short_description: Offline AI security camera agent for retail.
tags:
  - track:backyard
  - sponsor:openbmb
  - sponsor:nvidia
  - sponsor:openai
  - sponsor:cohere
---

# Eyas — AI Security Camera Agent

Eyas is an on-device security camera agent built for our teammate's family's convenience store — it runs person tracking, event detection, and LLM reasoning over CCTV footage to surface theft, loitering, and suspicious activity as a structured, searchable log. No cloud required.

## Features

- **Visual pipeline** — YOLO11n person tracking → MiniCPM-V 4.6 VLM observations → heuristic event structuring → Nemotron 3 Nano 4B LLM reasoning
- **Event Timeline** — scatter chart + table; click any row or dot to seek the annotated video
- **Event clips** — load a 6-second clip around any event; plays in the left video panel
- **Summary & Alerts** — risk gauge, flag breakdown pie chart, and overnight summary
- **Ask Footage** — natural-language Q&A about the event log via the on-device LLM
- **Detection Metrics** — per-zone bar chart and event density timeline
- **Audio Report** — spoken security brief via VoxCPM2 TTS
- **Clip Library** — stored clip manager (store, preview, delete, reload for analysis)
- **Language** — English and Korean; hot-swap in Settings without restarting
- **Resizable split layout** — drag handle between the left video panel and the right analysis tabs

## Models

| Model | Role | Size |
|---|---|---|
| [YOLO11n](https://github.com/ultralytics/ultralytics) | Person detector + BotSORT tracker | ~6 MB |
| [MiniCPM-V 4.6](https://huggingface.co/openbmb/MiniCPM-V-4.6) | Vision-language observer | ~1.3B params |
| [Nemotron 3 Nano 4B](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF) | LLM reasoner (GGUF Q4) | ~2.5 GB |
| [TinyAya](https://huggingface.co/CohereLabs/tiny-aya-global-GGUF) | Translation (GGUF Q4) | ~0.5 GB |
| [VoxCPM2](https://huggingface.co/openbmb/MiniCPM-o-2_6) | Text-to-speech | ~2.4B params |

All models download automatically on first run. No API keys required.

## Video filename convention

Eyas reads the **zone** and **recording time** from each video's filename. Use this pattern when naming clips before uploading:

```
YYYYMMDD_HHMMSS_<zone>.<ext>
```

Supported formats: `.mp4`, `.m4v` (and any format readable by OpenCV).

| Part | Format | Example |
|---|---|---|
| Date | 8-digit `YYYYMMDD` | `20260615` |
| Time | 6-digit `HHMMSS` | `130000` |
| Zone | any string (underscores allowed) | `aisle1`, `aisle2`, `aisle3`, `aisle4` |

**Examples**

```
20260615_130000_aisle1.m4v  → zone "aisle1", recorded 2026-06-15 at 13:00
20260615_130000_aisle2.m4v  → zone "aisle2", recorded 2026-06-15 at 13:00
20260615_130000_aisle3.m4v  → zone "aisle3"
20260615_130000_aisle4.m4v  → zone "aisle4"
```

If the filename does not match this pattern the pipeline falls back to a generic `review_area` zone that covers the full frame.

The six bundled sample clips already follow this convention:

| File | Zone | Source |
|---|---|---|
| `20260615_130000_aisle1.m4v` | `aisle1` | Filmed at Joy Convenience Store |
| `20260615_130000_aisle2.m4v` | `aisle2` | Filmed at Joy Convenience Store |
| `20260615_130000_aisle3.m4v` | `aisle3` | Filmed at Joy Convenience Store |
| `20260615_130000_aisle4.m4v` | `aisle4` | Filmed at Joy Convenience Store |
| `20260608_120000_entrance.mp4` | `entrance` | Online footage |
| `20260608_130000_counter.mp4` | `counter` | Online footage |

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

## Build workflows

### 1 — Local development (hot reload)

Run the Gradio backend and the Vite dev server side by side. In development,
the React app connects directly to Gradio on port 7860.

```bash
# Terminal 1 — Gradio backend
python eyas/app.py               # http://localhost:7860

# Terminal 2 — React dev server (hot reload)
(cd eyas/ui/frontend && npm install)
(cd eyas/ui/frontend && npm run dev)    # http://localhost:5173
```

Open `http://localhost:5173`. The frontend connects to the Gradio backend at
`http://127.0.0.1:7860`, so both servers must be running.

To use a different backend port, start both sides with matching values:

```bash
python eyas/app.py --port 7861
(cd eyas/ui/frontend && VITE_GRADIO_BACKEND_URL=http://127.0.0.1:7861 npm run dev)
```

### 2 — Production build (static files)

Vite compiles the SPA into `eyas/ui/dist/`. Gradio then serves those files as static assets — no separate Node process needed at runtime.

```bash
(cd eyas/ui/frontend && npm run build)    # → eyas/ui/dist/
python eyas/app.py
# Open http://localhost:7860
```

### 3 — Docker image

The [Dockerfile](Dockerfile) runs the frontend build and model pre-download as part of `docker build`, so the resulting image is self-contained.

Build order inside Docker:
1. **System deps** — libgl, Node 20, git-lfs
2. **`npm ci`** (package.json copied first for layer caching)
3. **`npm run build`** — outputs `eyas/ui/dist/`
4. **`llama-cpp-python`** from pre-built CPU wheels (no C++ compilation)
5. **Python deps** from `requirements.txt`
6. **App code** copied in
7. **`download_models.py`** — bakes YOLO and GGUF models into the image layer

```bash
docker build -t eyas .
docker run -p 7860:7860 eyas
# Open http://localhost:7860
```

Pass a Hugging Face token for gated models:

```bash
docker build --build-arg HF_TOKEN=hf_xxx -t eyas .
```

## Pushing changes

### Push to GitHub

```bash
git push origin main
```

### Push to Hugging Face Spaces

The repo has a `space` remote. Pushing to it triggers a Space build on HF infrastructure.

For ZeroGPU, switch the Space to the Gradio SDK in Hugging Face settings, set the hardware to ZeroGPU, and add `EYAS_ZERO_GPU=1` as a Space variable so model loading uses the GPU path.

HF Spaces has a 1 GB LFS storage limit. To avoid pushing the full git history (which includes old model-weight LFS objects), always use an orphan commit when deploying:

```bash
git checkout --orphan hf-deploy
git commit -m "Deploy to HF Spaces"
git push space hf-deploy:main --force
git checkout main
git branch -D hf-deploy
```

This creates a single root commit with only the current source tree. Git LFS only needs to upload the Korean font (~16 MB); everything else is either a small text file or gitignored.

> Sample videos in `eyas/input/` are committed directly (no LFS) so they ship with the HF build. Test fixtures in `eyas/tests/samples/` remain gitignored.

### Push to both at once

```bash
# GitHub — normal push
git push origin main

# HF Spaces — orphan deploy (see above)
git checkout --orphan hf-deploy && git commit -m "Deploy to HF Spaces" && git push space hf-deploy:main --force && git checkout main && git branch -D hf-deploy
```

Live space: [build-small-hackathon/eyas](https://huggingface.co/spaces/build-small-hackathon/eyas)

### 4 — Hugging Face Spaces (build details)

The [Dockerfile](Dockerfile) targets the free CPU tier on HF Spaces:

- `python:3.12-slim` (Debian trixie) base image
- Node 20 for the frontend build step (`npm run build` baked into the image)
- `llama-cpp-python` from pre-built CPU wheels — no C++ compilation, no build timeout
- YOLO and Nemotron/TinyAya downloaded at image build time via `eyas/scripts/download_models.py`
- MiniCPM-V and VoxCPM2 download on first startup (too large to bake in)

## Repository layout

```
eyas/
  app.py                  Entry point — loads prefs and launches Gradio
  object_detection/       YOLO11 + BotSORT tracker
  video_processing/       MiniCPM-V VLM wrapper
  event_structuring/      Heuristic event builder
  llm/                    Nemotron reasoner (llama.cpp)
  postprocessing/         Translation (TinyAya) + TTS (VoxCPM2)
  streaming/              Live camera capture
  storage/                Clip index
  ui/                     Gradio API + React frontend
    frontend/             React + Vite + MUI source
  utils/                  Shared helpers
  scripts/                CLI entry points
  models/                 Local weights (gitignored — auto-downloaded)
  input/                  Sample input videos
docs/                     Design and architecture notes
Dockerfile                HF Spaces deployment
scripts/download_models.py  Model pre-download for Docker build
```

## Docs

- [Architecture](docs/ARCHITECTURE.md) — pipeline diagram and component breakdown
- [AI Theft Detection](docs/AI_THEFT_DETECTION.md) — capabilities, limits, and best practices
- [Project Idea](docs/PROJECT_IDEA.md) — original concept and scope

Agent-assisted changes are attributed in their commit metadata.
