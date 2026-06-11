---
title: Eyas — AI Security Camera Agent
emoji: 🦅
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Eyas — AI Security Camera Agent

An offline-first security camera agent built for the **Build Small Hackathon**. Upload a CCTV clip and Eyas runs a full detection → observation → reasoning pipeline on local small models, then presents the results in an interactive split-panel UI.

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

## Quick start

```bash
cd eyas
python3 -m venv .venv
source .venv/bin/activate      # macOS / Linux
# .venv\Scripts\activate       # Windows

pip install -r requirements.txt
python app.py
# Open http://localhost:7860
```

Korean UI:

```bash
python app.py --lang ko
```

## Frontend development

The UI is a React + Vite SPA. Gradio runs as a pure API backend; the built static files are served directly.

```bash
cd eyas/ui/frontend
npm install
npm run dev        # http://localhost:5173 — proxies /gradio_api to port 7860
npm run build      # outputs to eyas/ui/dist/
```

## Docker

```bash
docker build -t eyas .
docker run -p 7860:7860 eyas
```

Pass a Hugging Face token if any models require gated access:

```bash
docker build --build-arg HF_TOKEN=hf_xxx -t eyas .
```

## Deployment (Hugging Face Spaces)

The [Dockerfile](Dockerfile) targets the free CPU tier on HF Spaces:

- `python:3.12-slim` (Debian trixie) base image
- Node 20 for the frontend build step
- `llama-cpp-python` installed from pre-built CPU wheels — no C++ compilation, no build timeout
- YOLO and Nemotron/TinyAya downloaded at image build time via [`scripts/download_models.py`](scripts/download_models.py)
- MiniCPM-V and VoxCPM2 download on first startup (too large to bake in)

Live space: [build-small-hackathon/eyas](https://huggingface.co/spaces/build-small-hackathon/eyas)

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
    frontend/             React + Vite + Tailwind source
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
