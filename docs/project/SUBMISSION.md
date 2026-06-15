# Eyas — Submission

<p align="center">
  <img src="../assets/build-small-hackathon-checklist.png" alt="Build Small Hackathon checklist" width="700" />
</p>

**Project**: Eyas — AI Security Camera Agent  
**Team**: Javier Huang, Hanhee Lee, Joe Lee  
**Space**: [build-small-hackathon/eyas](https://huggingface.co/spaces/build-small-hackathon/eyas)  
**Track**: Backyard AI

---

## What we built

Eyas is an on-device security camera agent built for our teammate's family's convenience store. It runs person tracking, event detection, and LLM reasoning over CCTV footage to surface theft, loitering, and suspicious activity as a structured, searchable log.

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

The checklist below explains why Eyas is the strongest submission for the Backyard AI track. Eyas was built for a real person — the owners of our teammate's family's Korean-owned convenience store — who today manually scrub overnight CCTV footage after suspected theft. We demoed on real four-camera aisle footage filmed at Joy Convenience Store (a convenience store used as our filming location, with the same layout and CCTV setup as our target), and the full pipeline — tracking, event log, bilingual summary, spoken audio brief — ran on that footage and produced reports the store operators could read immediately. The problem is specific, the user is real, and the evidence is on film.

- [x] **Specific, real problem** — Small retail owners have no affordable tool to automatically review CCTV footage for theft, loitering, and unusual activity. Manual review of 8-hour overnight recordings is impractical.
- [x] **Built for a real person** — Built for our teammate's family, who runs a small Korean-owned convenience store. The tool runs on their existing laptop with no subscription, no cloud account, and no API keys.
- [x] **Evidence of real use** — Demo filmed at Joy Convenience Store (our filming location; same layout and CCTV profile as the target store). Pipeline run on actual four-camera aisle footage. Field notes at [FIELD_NOTES.md](FIELD_NOTES.md).
- [x] **Honest small-model fit** — Total loaded weight ~8.7 B params / ~6 GB. Runs fully on a laptop CPU; GPU optional.
- [x] **Polished Gradio app** — Custom React + MUI frontend; resizable panels; scatter-chart event timeline; animated splash; dark/light mode.

---

## Hard Constraints

The checklist below explains why Eyas satisfies all three hard constraints. The full model stack totals ~8.7 B parameters — well under the 32 B ceiling, with no single model exceeding 4 B. All pipeline logic is exposed through a `gr.Blocks` Gradio app; the custom React SPA is layered on top but does not replace the Gradio backend. The Space is live on HF Spaces CPU tier, and the demo video shows the full pipeline end-to-end.

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

The checklist below explains our Bonus Quest coverage. Eyas qualifies for 5 of the 6 available quests. The single missing one — Well-Tuned — would require labelled retail-theft training data we did not have time to collect; every other quest is fulfilled by load-bearing components already in the pipeline.

- [x] **Off the Grid** — Zero cloud API calls at inference time. YOLO via `ultralytics`, VLM via `transformers` locally, both LLMs via `llama-cpp-python` from GGUF weights on disk. Fully offline after the one-time model download.
- [ ] **Well-Tuned** — No custom fine-tuning. All models used off-the-shelf. *(Potential: fine-tune YOLO on retail theft datasets.)*
- [x] **Off-Brand** — The entire UI is a custom React + Vite + MUI SPA served as static files. Gradio is invisible to the user and acts as a pure API layer. No default Gradio component styling is visible. See [OFF_BRAND.md](../architecture/OFF_BRAND.md).
- [x] **Llama Champion** — Nemotron 3 Nano 4B and TinyAya Global both run through `llama-cpp-python` with Q4_K_M GGUF quantization. Metal on Apple Silicon; CPU fallback on HF Spaces.
- [x] **Sharing is Caring** — Agent traces published to the Hugging Face Hub at [sehyunlee217/Codex-Agent-Trace](https://huggingface.co/datasets/sehyunlee217/Codex-Agent-Trace).
- [x] **Field Notes** — [FIELD_NOTES.md](FIELD_NOTES.md) covers the pipeline design decisions, per-model lessons, what surprised us, and what we would do differently.

---

## Sponsor Awards

Each sponsor's model below is a required, load-bearing stage in the Eyas pipeline. Removing any one of them breaks a specific output — not a peripheral integration but a named tab or core capability that stops working without it.

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

### Cohere / TinyAya

- [x] **TinyAya Global** (`CohereLabs/tiny-aya-global-GGUF`) handles all freeform Korean translation — VLM activity text, scene descriptions, LLM summaries, Q&A replies, and TTS input.
- [x] Balances against a static string catalog (`i18n.js` / `locale.py`) for fixed labels to keep translation calls minimal and fast.

### Modal Awards

- [ ] Not deployed on Modal. *(Could add a Modal deployment path alongside Docker/HF Spaces.)*

---

## Special Awards

The entries below are Special Awards where Eyas has a specific, demonstrable claim — not aspirational entries. Each description explains what was actually built and why it satisfies the award criteria.

- [x] **Off-Brand Award** (`$1,500`) — Gradio's native component library is not used at all. The interface is a React 19 + Vite 8 + MUI 6 SPA compiled to static files and served by FastAPI alongside the Gradio process. All Gradio `Blocks` components are hidden; the frontend calls Gradio exclusively through the `@gradio/client` JS SDK streaming API. The result is a resizable split-panel security dashboard — video left, tabbed analysis right — that would be impossible to build within Gradio's component constraints. Full write-up in [OFF_BRAND.md](../architecture/OFF_BRAND.md).
- [x] **Best Agent** (`$1,000`) — Six models work in sequence with no human intervention between stages: YOLO11n tracks people → MiniCPM-V observes each track and outputs structured JSON → a heuristic event structurer merges observations and resolves pickup ambiguity → Nemotron 3 Nano reasons over the full event log → TinyAya translates output to Korean → VoxCPM2 narrates a spoken brief. Each stage produces structured output that the next stage consumes; the chain runs end-to-end from raw video to spoken security report with a single button press.
- [x] **Tiny Titan** (`$1,500`) — Six models totaling ~8.7 B parameters run on a laptop CPU with no GPU requirement. MiniCPM-V (1.3B) and VoxCPM2 (2.4B) use PyTorch; Nemotron (4B) and TinyAya (1B) run via llama-cpp-python with Q4_K_M GGUF quantization, which brings both under 3 GB combined on disk. The system was built and tested on standard consumer hardware and deployed to a CPU-tier HF Space.
- [x] **Best Demo** (`$1,000`) — The demo shows the full pipeline end-to-end on four-camera footage from a real operating store: batch upload → YOLO tracking with annotated bounding boxes → event timeline with click-to-seek → cross-camera Summary & Alerts → Ask Footage Q&A → spoken Audio Report. Every tab is used. The subject is a genuine security use case, not a toy dataset.
- [x] **Bonus Quest Champion** (`$2,000`) — 5 of 6 quests fulfilled: Off the Grid (fully offline inference), Off-Brand (custom React SPA), Llama Champion (two GGUF models via llama.cpp), Sharing is Caring ([Codex agent traces on HF Hub](https://huggingface.co/datasets/sehyunlee217/Codex-Agent-Trace)), Field Notes ([FIELD_NOTES.md](FIELD_NOTES.md)). Only Well-Tuned (fine-tuning) is missing.
- [ ] **Judges' Wildcard** (`$1,000`)
- [ ] **Community Choice** (`$2,000`)

---

## Open Items

| Item | Status |
|---|---|
| Record demo video (full pipeline, all tabs visible) | ✅ Filmed at Joy Convenience Store (demo filming location) |
| Real-user evidence | ✅ Target: teammate's family's store. Demo footage: Joy Convenience Store. See [FIELD_NOTES.md](FIELD_NOTES.md) |
| Field Notes | ✅ [FIELD_NOTES.md](FIELD_NOTES.md) |
| Model documentation (one doc per model) | ✅ [docs/models/](../models/) |
| Architecture diagram embedded in docs | ✅ ARCHITECTURE.md + README |
| Codex contributions documented | ✅ [CODEX.md](CODEX.md) |
| Write social-media post (Twitter / LinkedIn / HF forums) | ⬜ TODO |
| Publish Codex traces to HF Hub (Sharing is Caring) | ✅ [sehyunlee217/Codex-Agent-Trace](https://huggingface.co/datasets/sehyunlee217/Codex-Agent-Trace) |
