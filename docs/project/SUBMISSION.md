# Eyas — Submission

**Project**: Eyas — AI Security Camera Agent  
**Team**: Javier Huang, Hanhee Lee, Joe Lee  
**Space**: [build-small-hackathon/eyas](https://huggingface.co/spaces/build-small-hackathon/eyas)  
**Track**: Backyard AI

---

## What we built

Eyas is an on-device security camera agent built for our teammate's family's convenience store. It runs an automated pipeline over CCTV footage to surface theft, loitering, and suspicious activity as a structured, searchable log — replacing hours of manual footage review with a single click.

### Visual pipeline

The core pipeline chains five models end-to-end with no cloud APIs:

1. **YOLO11n + BotSORT** — detects and tracks people across frames, maintaining consistent track IDs through shelf occlusions using Re-ID
2. **MiniCPM-V 4.6** — watches each tracked person through a sliding evidence window and outputs structured JSON: activity, held objects, and whether a pickup occurred
3. **Heuristic event structurer** — merges per-track observations, applies keyword-based overrides when the VLM hedges on confirmed pickups, assigns zone labels from filename conventions
4. **Nemotron 3 Nano 4B** — reads the event log and produces a risk-level summary, flags, suspicious clip list, and answers natural-language Q&A
5. **TinyAya Global** — translates all freeform VLM and LLM text to Korean on demand
6. **VoxCPM2** — synthesizes a spoken audio security brief from the LLM summary

### UI — custom React SPA over Gradio API

The entire interface is a React + Vite + MUI SPA. Gradio runs as a pure API backend with all native components hidden. The frontend communicates via `@gradio/client` and the Gradio streaming endpoint:

- **Event Timeline** — Recharts scatter chart cross-linked with a MUI table; clicking a row or dot seeks all video elements simultaneously to that timestamp
- **Summary & Alerts** — risk gauge, flag breakdown, per-camera narrative sections when multiple clips are loaded
- **Ask Footage** — Q&A chat; the session summary is injected as authoritative context so the LLM can't contradict its own analysis
- **Detection Metrics** — per-zone bar chart and event-frequency timeline
- **Audio Report** — streams spoken output via VoxCPM2 TTS with live progress phases
- **Resizable split layout** — drag handle between queue/analysis and footage preview panels
- **Multi-camera grid** — 2×2 synchronized grid view with per-camera event highlighting; timed sync-lock prevents seek echo loops
- **ClipViewSelector** — "All" chip for the unified session view, per-clip chips for single-camera drill-down
- **Dark/light mode** — Eyas falcon palette (navy/yellow dark, warm-yellow/blue light), persisted in localStorage
- **Splash screen** — animated per-model loading progress before the main UI appears

### Multi-camera session

Multiple clips (one per camera angle) can be queued and processed sequentially. Events from each clip are merged into a unified session event list tagged with `source_video` and `source_clip_id`. After all clips complete, `summarize_session` generates a cross-camera LLM narrative with per-camera breakdowns.

### Korean localization

Full localization without restart:
- Static strings (tab labels, chip names, zone labels, UI text) live in `i18n.js` and `locale.py` as hardcoded Korean equivalents — no model call needed
- Freeform VLM/LLM text (`activity`, `description`, `summary`, Q&A replies) is translated live via TinyAya GGUF
- Language hot-swap triggers parallel localization of the full session snapshot in a single round-trip
- Korean bounding-box overlays on the annotated video are rendered with the bundled Noto Sans CJK font

### Engineering highlights

- **Pickup accuracy** — VLMs tend to hedge; a `=== CONFIRMED PICKUPS ===` roster is injected before every LLM prompt so the model cannot overlook confirmed events regardless of context pressure
- **Context management** — event log is budget-trimmed for Nemotron's 4096-token window; multi-camera sessions distribute the budget proportionally per camera; pickup events are never trimmed
- **Session restore** — pipeline state (events, summaries, annotated videos, queue) is persisted on the server and restored on page reload without re-running the pipeline
- **Session export** — ZIP download of the full session: annotated videos, event JSON, summary, and audio report
- **Model memory management** — models are lazy-loaded and explicitly unloaded between pipeline stages to avoid OOM on ZeroGPU's ephemeral GPU allocation
- **HF Spaces deploy** — orphan-branch push strategy keeps the Space at a single root commit; Vite bundle is pre-built and committed so HF doesn't need to run npm
- **Annotated video** — OpenCV `VideoWriter` with `avc1` (H.264) fourcc for browser-compatible MP4; SUSPICIOUS (red) and OBSERVING (orange) bounding box overlays with persistent state labels

---

## Main Track: Backyard AI

- [x] **Specific, real problem** — Small retail owners have no affordable tool to automatically review CCTV footage for theft, loitering, and unusual activity. Manual review of 8-hour overnight recordings is impractical.
- [x] **Built for a real person** — Built for our teammate's family who runs Joy Convenience Store. The tool runs on their existing laptop with no subscription, no cloud account, and no API keys.
- [x] **Evidence of real use** — Demo filmed at Joy Convenience Store on actual four-camera aisle footage. The family reviewed the event timeline and per-zone summary on their own recordings. Field notes at [FIELD_NOTES.md](FIELD_NOTES.md).
- [x] **Honest small-model fit** — Total loaded weight ~8.7 B params / ~6 GB. Runs fully on a laptop CPU; GPU optional.
- [x] **Polished Gradio app** — Custom React + MUI frontend; resizable panels; scatter-chart event timeline; animated splash; dark/light mode.

---

## Hard Constraints

- [x] **≤ 32 B parameters total**

  | Model | Role | Params |
  |---|---|---|
  | YOLO11n | Person detector + BotSORT tracker | ~3 M |
  | MiniCPM-V 4.6 | Vision-language observer | ~1.3 B |
  | Nemotron 3 Nano 4B | LLM reasoner (GGUF Q4) | ~4 B |
  | TinyAya Global | Korean translation (GGUF Q4) | ~1 B |
  | VoxCPM2 | TTS audio brief | ~2.4 B |
  | **Total** | | **~8.7 B** |

- [x] **Gradio app** — `eyas/app.py` is a `gr.Blocks` app; all pipeline logic is exposed as Gradio API endpoints consumed by the React frontend via `@gradio/client`.
- [x] **Hugging Face Space** — [build-small-hackathon/eyas](https://huggingface.co/spaces/build-small-hackathon/eyas) (CPU tier; ZeroGPU-ready via `EYAS_ZERO_GPU=1`).
- [x] **Demo video** — Filmed at Joy Convenience Store. Shows the full pipeline: multi-clip upload → YOLO tracking → VLM captioning → event timeline → Summary & Alerts → Ask Footage Q&A → Audio Report.
- [ ] **Social-media post** — *(Draft and post before final submission.)*

---

## Bonus Quests

- [x] **Off the Grid** — Zero cloud API calls at inference time. YOLO via `ultralytics`, VLM via `transformers` locally, both LLMs via `llama-cpp-python` from GGUF weights on disk. Fully offline after the one-time model download.
- [ ] **Well-Tuned** — No custom fine-tuning. All models used off-the-shelf. *(Potential: fine-tune YOLO on retail theft datasets.)*
- [x] **Off-Brand** — The entire UI is a custom React + Vite + MUI SPA served as static files. Gradio is invisible to the user and acts as a pure API layer. No default Gradio component styling is visible. See [OFF_BRAND.md](../architecture/OFF_BRAND.md).
- [x] **Llama Champion** — Nemotron 3 Nano 4B and TinyAya Global both run through `llama-cpp-python` with Q4_K_M GGUF quantization. Metal on Apple Silicon; CPU fallback on HF Spaces.
- [ ] **Sharing is Caring** — Agent traces stored in `docs/codex-traces/` locally but not yet published to the Hub.
- [x] **Field Notes** — [FIELD_NOTES.md](FIELD_NOTES.md) covers the pipeline design decisions, per-model lessons, what surprised us, and what we would do differently.

---

## Sponsor Awards

### OpenBMB (`$10,000` total)

- [x] **MiniCPM-V 4.6** is the core visual observer — every detected person is described by the VLM (activity, held objects, pickup confirmation). Loaded via Hugging Face Transformers from the official `openbmb/MiniCPM-V-4.6` repo.
- [x] **VoxCPM2** (`openbmb/VoxCPM2`) generates the spoken audio security brief. Supports MPS, CPU, and ZeroGPU burst via the `voxcpm` package.
- [x] Both models are load-bearing: MiniCPM-V is the only path from pixels to structured events; VoxCPM2 is the only TTS in the stack.

### NVIDIA Nemotron Quest (2× RTX 5080)

- [x] **Nemotron 3 Nano 4B** (Q4_K_M GGUF) is the primary reasoning model — summarizes event logs, assigns risk levels (`none` / `low` / `medium` / `high` / `critical`), answers natural-language Q&A, and generates alert narratives for the audio brief.
- [x] Runs via `llama-cpp-python` from the official `nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF` checkpoint.
- [x] Nemotron is load-bearing: without it, the Summary & Alerts, Ask Footage, and Audio Report tabs have no content.

### OpenAI Track (`$10,000` total)

- [x] All Codex-assisted development is attributed via `Co-Authored-By: Codex <codex@openai.com>` git trailers. Full session reasoning traces in [`docs/codex-traces/`](../codex-traces/). See [CODEX.md](CODEX.md) for the commit-by-commit breakdown.
- [ ] No OpenAI inference models used at runtime.

### Cohere / TinyAya

- [x] **TinyAya Global** (`CohereLabs/tiny-aya-global-GGUF`) handles all freeform Korean translation — VLM activity text, scene descriptions, LLM summaries, Q&A replies, and TTS input.
- [x] Balances against a static string catalog (`i18n.js` / `locale.py`) for fixed labels to keep translation calls minimal and fast.

### Modal Awards

- [ ] Not deployed on Modal. *(Could add a Modal deployment path alongside Docker/HF Spaces.)*

---

## Special Awards

- [x] **Off-Brand Award** (`$1,500`) — Strongest candidate. The UI is a fully custom React 19 + Vite 8 + MUI 6 SPA. Gradio owns zero pixels; all its native components are hidden. The frontend communicates with Gradio exclusively via the JS SDK streaming API.
- [x] **Best Agent** (`$1,000`) — Five-model agentic chain: YOLO detects → MiniCPM-V observes → heuristic structurer reasons → Nemotron synthesizes → TinyAya translates → VoxCPM2 narrates. Each stage's output is the next stage's input.
- [x] **Tiny Titan** (`$1,500`) — 8.7 B total params, fully CPU-capable, no GPU required. Fits within the "laptop" framing of the hackathon.
- [ ] **Best Demo** (`$1,000`) — Depends on video quality. Show the full pipeline end-to-end: upload → analysis → annotated video + timeline + audio report, all on real convenience store footage.
- [x] **Bonus Quest Champion** (`$2,000`) — 4 of 6 quests fulfilled: Off the Grid, Off-Brand, Llama Champion, Field Notes.
- [ ] **Judges' Wildcard** (`$1,000`) — No specific action; polish and story matter.
- [ ] **Community Choice** (`$2,000`) — Needs HF community engagement; post on HF forums and social media.

---

## Open Items

| Item | Status |
|---|---|
| Record demo video (full pipeline, all tabs visible) | ✅ Filmed at Joy Convenience Store |
| Real-user evidence | ✅ Joy Convenience Store field test in [FIELD_NOTES.md](FIELD_NOTES.md) |
| Field Notes | ✅ [FIELD_NOTES.md](FIELD_NOTES.md) |
| Model documentation (one doc per model) | ✅ [docs/models/](../models/) |
| Architecture diagram embedded in docs | ✅ ARCHITECTURE.md + README |
| Codex contributions documented | ✅ [CODEX.md](CODEX.md) |
| Write social-media post (Twitter / LinkedIn / HF forums) | ⬜ TODO |
| Verify Space runs cleanly on CPU tier end-to-end | ⬜ TODO |
| Publish Codex traces to HF Hub (Sharing is Caring) | ⬜ Optional |
| Modal deployment path | ⬜ Optional |
