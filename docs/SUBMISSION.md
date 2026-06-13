# Eyas — Hackathon Submission Checklist

**Project**: Eyas — AI Security Camera Agent  
**Space**: [build-small-hackathon/eyas](https://huggingface.co/spaces/build-small-hackathon/eyas)  
**Track**: Backyard AI  

---

## Main Track: Backyard AI

> Build something for a real person you actually know. Solve a specific problem that measurably improves their day.

- [x] **Specific, real problem** — Small retail and property owners rely on CCTV but have no affordable tool to automatically review footage for theft, loitering, and unusual activity. Reviewing hours of footage manually is impractical.
- [x] **Intended for a real person** — Built for our teammate's family, who runs Joy Convenience Store and wanted to stop scrubbing through overnight recordings by hand. The tool runs on their existing laptop with no subscription or cloud account required.
- [x] **Evidence of real use** — Demo video filmed at Joy Convenience Store (our teammate's family's shop). Pipeline runs on actual aisle footage from four cameras; the family reviewed the event timeline and per-zone activity summary on their own footage.
- [x] **Honest fit with the small-model constraint** — Every model is well under 32 B params. Total loaded weight at runtime is ~6 GB (GGUF Q4 LLMs + VLM). Runs on a laptop CPU; GPU optional.
- [x] **Polished Gradio app** — Custom React + MUI frontend served via `gr.Server`; resizable split panels, event timeline, Q&A, audio brief, clip library.

---

## Hard Constraints

- [x] **≤ 32 B parameters total**

  | Model | Role | Params |
  |---|---|---|
  | YOLO11n | Person detector + BotSORT tracker | ~3 M |
  | MiniCPM-V 4.6 | Vision-language observer | ~1.3 B |
  | Nemotron 3 Nano 4B | LLM reasoner (GGUF Q4) | ~4 B |
  | TinyAya | Translation (GGUF Q4) | ~1 B |
  | VoxCPM2 | TTS audio brief | ~2.4 B |
  | **Total** | | **~8.7 B** |

- [x] **Gradio app** — `eyas/app.py` is a Gradio Blocks app; all pipeline logic exposed as Gradio API endpoints consumed by the React frontend.
- [x] **Hosted on a Hugging Face Space** — [build-small-hackathon/eyas](https://huggingface.co/spaces/build-small-hackathon/eyas) (CPU tier; ZeroGPU-ready via `EYAS_ZERO_GPU=1`).
- [x] **Short demo video** — Filmed at Joy Convenience Store. Shows full pipeline: multi-clip batch upload → YOLO tracking → VLM captioning → event timeline → Summary & Alerts (per-cam breakdown) → Ask Footage Q&A.
- [ ] **Social-media post** — *(Draft and post before final submission.)*

---

## Bonus Quests

- [x] **Off the Grid** — Zero cloud API calls. YOLO runs via `ultralytics`, VLM via `transformers` locally, both LLMs via `llama-cpp-python` from GGUF weights downloaded to disk. No API keys required; works fully offline after the one-time model download.
- [ ] **Well-Tuned** — No custom fine-tuning applied. All models are used off-the-shelf. *(Could be addressed by fine-tuning YOLO on retail theft datasets.)*
- [x] **Off-Brand** — The entire UI is a custom React + Vite + MUI SPA served as static files via `gr.Server`. None of the default Gradio component styling is visible to the end user. Includes resizable drag-handle split panels, icon-only hover-expand sidebar, scatter-chart event timeline, and animated splash screen.
- [x] **Llama Champion** — Nemotron 3 Nano 4B and TinyAya both run through `llama-cpp-python` with GGUF quantisation (Q4_K_M). Metal acceleration on Apple Silicon; CPU fallback for HF Spaces.
- [ ] **Sharing is Caring** — Agent traces not yet published to the Hub. *(Could export event logs + LLM reasoning chains as a dataset.)*
- [x] **Field Notes** — [FIELD_NOTES.md](FIELD_NOTES.md) covers the pipeline design decisions, per-model lessons, what surprised us, and what we would do differently.

---

## Sponsor Awards

### OpenBMB Awards (`$10,000` total)
OpenBMB sponsors awards for strong use of their model family.

- [x] Uses **MiniCPM-V 4.6** as the core visual observer — every detected person is described by the VLM (activity, held objects, pickup confirmation).
- [x] Uses **VoxCPM2** (`MiniCPM-o-2_6`) for the spoken audio security brief.
- [x] Both models are loaded from Hugging Face Hub (official OpenBMB repos).

### NVIDIA Nemotron Quest (2× RTX 5080)
Standout builds using Nemotron models.

- [x] **Nemotron 3 Nano 4B** is the primary reasoning model — summarises event logs, assigns risk levels, answers natural-language questions about footage, generates alert narratives.
- [x] Runs via llama-cpp-python with the official NVIDIA GGUF Q4_K_M checkpoint.
- [x] Nemotron is load-bearing: without it the Summary, Ask Footage, and Audio Report tabs have no content.

### OpenAI Track (`$10,000` total)
- [ ] No OpenAI models used. Not applicable unless track criteria are broader than model usage.

### Modal Awards (credits)
- [ ] Not deployed on Modal. *(Could add a Modal deployment path alongside Docker/HF Spaces.)*

---

## Special Awards

- [x] **Off-Brand Award** (`$1,500`) — Strongest candidate. Fully custom React frontend; Gradio is invisible to the user and acts as a pure API layer.
- [x] **Best Agent** (`$1,000`) — The pipeline is an agentic multi-model chain: YOLO detects → MiniCPM-V observes → heuristic structurer reasons → Nemotron synthesises → TinyAya translates → VoxCPM2 narrates. Each stage feeds the next; the LLM has tool-like access to the structured event list.
- [ ] **Tiny Titan** (`$1,500`) — Sub-10 B total params and CPU-only operation is a strong angle; worth calling out explicitly in the demo.
- [ ] **Best Demo** (`$1,000`) — Depends on video quality. *(Show the full pipeline end-to-end on real footage with the annotated video, timeline, and audio report all in frame.)*
- [ ] **Bonus Quest Champion** (`$2,000`) — Currently 3 of 6 quests fulfilled (Off the Grid, Off-Brand, Llama Champion). Adding Field Notes (blog post) is the lowest-effort fourth quest.
- [ ] **Judges' Wildcard** (`$1,000`) — No specific action; polish and story matter.
- [ ] **Community Choice** (`$2,000`) — Needs HF community engagement; post on HF forums and social media.

---

## Before Submission — Open Items

| Item | Status |
|---|---|
| Record demo video (full pipeline run, all tabs visible) | ✅ Done — filmed at Joy Convenience Store |
| Write social-media post (Twitter / LinkedIn / HF forums) | ⬜ TODO |
| Add real-user evidence / quote to README or demo | ✅ Done — Joy Convenience Store field test in FIELD_NOTES.md |
| Write Field Notes blog post | ✅ Done — [FIELD_NOTES.md](FIELD_NOTES.md) |
| Verify Space runs cleanly on CPU tier end-to-end | ⬜ TODO |
| Add Nemotron + OpenBMB model cards to Space README | ⬜ TODO |
