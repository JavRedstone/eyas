---
title: Eyas
emoji: 🦅
colorFrom: blue
colorTo: yellow
pinned: true
sdk: gradio
sdk_version: 5.38.0
python_version: "3.12"
app_file: eyas/app.py
license: mit
short_description: AI Security Camera Agent
tags:
  - track:backyard
  - sponsor:openbmb
  - sponsor:nvidia
  - sponsor:openai
  - sponsor:cohere
  - achievement:offgrid
  - achievement:offbrand
  - achievement:llama
  - achievement:sharing
  - achievement:fieldnotes
---

<p align="center">
  <img src="docs/assets/eyas_logo_wide.png" alt="Eyas" width="600" />
</p>

# Eyas: AI Security Camera Agent

| | Name | HuggingFace |
|---|---|---|
| | Javier Huang | [@JavRedstone](https://huggingface.co/JavRedstone) |
| | Hanhee Lee | [@hanheelee](https://huggingface.co/hanheelee) |
| | Joe Lee | [@sehyunlee217](https://huggingface.co/sehyunlee217) |

**[HuggingFace Space](https://huggingface.co/spaces/build-small-hackathon/eyas)** · **[GitHub](https://github.com/JavRedstone/eyas)** · **[Demo Video](https://www.youtube.com/watch?v=x9h7nMv_KeQ)**

Eyas is an on-device security camera agent built for our teammate's family's convenience store. It runs person tracking, event detection, and LLM reasoning over CCTV footage to surface theft, loitering, and suspicious activity as a structured, searchable log.

---

## What it does

- **Visual pipeline** — person tracking → VLM observation → event structuring → LLM reasoning
- **Event Timeline** — scatter chart + table; click any event to seek the annotated video
- **Summary & Alerts** — risk gauge, flag breakdown, and per-camera narrative
- **Ask Footage** — natural-language Q&A over the event log via the on-device LLM
- **Audio Report** — spoken security brief via VoxCPM2 TTS
- **Multi-camera** — queue multiple clips, get a unified cross-camera session summary
- **Korean** — full UI and pipeline output translation, hot-swap without restart

## Architecture

<p align="center">
  <img src="docs/assets/eyas-architecture-diagram.png" alt="Eyas architecture diagram" width="900" />
</p>

## Models

| Model | Role | Size |
|---|---|---|
| [YOLO11n](https://github.com/ultralytics/ultralytics) | Person detector + BotSORT tracker | ~6 MB |
| [MiniCPM-V 4.6](https://huggingface.co/openbmb/MiniCPM-V-4.6) | Vision-language observer | ~1.3B params |
| [Nemotron 3 Nano 4B](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF) | LLM reasoner (GGUF Q4) | ~2.5 GB |
| [TinyAya Global](https://huggingface.co/CohereLabs/tiny-aya-global-GGUF) | Korean translation (GGUF Q4) | ~0.5 GB |
| [VoxCPM2](https://huggingface.co/openbmb/MiniCPM-o-2_6) | Text-to-speech | ~2.4B params |

All models download automatically on first run. No API keys required.

---

## Docs

**Guides**

| Document | Contents |
|---|---|
| [Setup & Development](docs/guides/SETUP.md) | Quick start, local dev, Docker, HF Spaces deploy |
| [AI Theft Detection](docs/guides/AI_THEFT_DETECTION.md) | Capabilities, limits, and best practices |
| [Codex Contributions](docs/project/CODEX.md) | Agent-assisted commits, reasoning traces |

**Architecture**

| Document | Contents |
|---|---|
| [Architecture](docs/architecture/ARCHITECTURE.md) | Pipeline diagram, component breakdown, event schema |
| [Off-Brand Frontend](docs/architecture/OFF_BRAND.md) | Why and how the UI is a React SPA instead of Gradio components |

**Models**

| Document | Contents |
|---|---|
| [YOLO11n](docs/models/yolo11n.md) | Person detection + BotSORT tracking |
| [MiniCPM-V 4.6](docs/models/minicpm-v.md) | Vision-language observer (VLM) |
| [Nemotron 3 Nano 4B](docs/models/nemotron-nano.md) | LLM reasoner — summary, Q&A, alerts |
| [TinyAya Global](docs/models/tinyaya.md) | Korean translation |
| [VoxCPM2](docs/models/voxcpm2.md) | Text-to-speech audio report |

**Project**

| Document | Contents |
|---|---|
| [Field Notes](docs/project/FIELD_NOTES.md) | Build log — design decisions, lessons from each stage, store field test |
| [Submission](docs/project/SUBMISSION.md) | Hackathon checklist and what we built |
| [Hackathon](docs/project/HACKATHON.md) | Track info and award categories |

Live space: [build-small-hackathon/eyas](https://huggingface.co/spaces/build-small-hackathon/eyas)
