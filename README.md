---
title: Eyas — AI Security Camera Agent
emoji: 🦅
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# HuggingFace Build Small Hackathon — Project Workspace

This workspace contains materials and a prototype plan for a Hackathon submission built around small, local models.

Docs
- `docs/HACKATHON.md` — hackathon overview and rules
- `docs/PLAN.md` — step-by-step build plan
- `docs/PROJECT_IDEA.md` — Offline CCTV Security Assistant project idea
- `docs/ARCHITECTURE.md` — processing pipeline and model choices
- `docs/AI_THEFT_DETECTION.md` — practical overview of AI theft-detection capabilities and limits

Quick start (prototype)
1. Navigate to the `eyas/` directory and create a virtual environment there:

```bash
cd eyas
python3 -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate      # macOS / Linux
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the Gradio prototype

```bash
python app.py
# or
gradio app.py
```

The Nemotron GGUF for the LLM reasoner downloads automatically from Hugging Face on first use. Set `EYAS_MODEL_PATH` only if you want to point the app at a local GGUF file.

Notes
- The repository currently contains design docs and plans; code and models may be added in later commits.
- See `docs/` for design, model choices, and deployment notes.