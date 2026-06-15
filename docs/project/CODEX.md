# Codex Contributions to Eyas

This document records the work done by [OpenAI Codex](https://openai.com/codex) on the Eyas pipeline during the Build Small Hackathon.
All Codex commits carry the git co-author trailer `Co-Authored-By: Codex <codex@openai.com>` and can be verified on GitHub.

Full session-by-session reasoning traces are stored in [`docs/../codex-traces/`](../codex-traces/) as JSONL files.

---

## What Codex worked on

### Multi-camera video grid (All-view)

Built the "All Cameras" view — a synchronized multi-camera grid that loads raw feeds on page open and switches to annotated video after analysis. Includes per-camera highlighting when clicking an event chip, sync-lock to prevent echo loops between video elements, and the `ClipViewSelector` component for switching between single-camera and session views.

- [`3d004030`](https://github.com/JavRedstone/eyas/commit/3d004030) — All-view: multi-cam grid with sync and clip highlighting
- [`f68e3e35`](https://github.com/JavRedstone/eyas/commit/f68e3e35) — All-view: raw-feed grid on load, annotated grid after analysis
- [`5becbc18`](https://github.com/JavRedstone/eyas/commit/5becbc18) — Fix video grid sync echo loop with timed lock
- [`cf40527f`](https://github.com/JavRedstone/eyas/commit/cf40527f) — All-view: render full SummaryAlerts output per clip below total summary
- [`21291cd7`](https://github.com/JavRedstone/eyas/commit/21291cd7) — All-view: per-cam summaries + LLM total, cross-cam person matching

### LLM summary quality

Identified and fixed a chain of issues causing the LLM to say "no pickup occurred" despite confirmed pickup events in the log. Added programmatic pickup roster injection, improved event trimming, fixed the risk-rank comparison bug, and wired the generated summary into the Q&A prompt so the model cannot contradict its own analysis.

- [`774b07f0`](https://github.com/JavRedstone/eyas/commit/774b07f0) — Fix total summary contradicting per-camera findings
- [`92d8f30a`](https://github.com/JavRedstone/eyas/commit/92d8f30a) — Fix LLM saying 'no pickup' despite YES event; improve trim strategy
- [`24b531a4`](https://github.com/JavRedstone/eyas/commit/24b531a4) — Fix summary quality: enforce pickup mention, fix total text, clean per-cam layout
- [`e1e16546`](https://github.com/JavRedstone/eyas/commit/e1e16546) — Fix NameError in pickup roster injection; truncate VLM scene bleed in item names
- [`4d7f5a2a`](https://github.com/JavRedstone/eyas/commit/4d7f5a2a) — Use session summary as authoritative context for Q&A

### Event timeline and UI fixes

Renamed the ambiguous "suspicious" chip to "handling", added the Activity field to event detail expansion, fixed the per-camera flags/clips rendering inside the wrong section card, and reduced the LLM input budget to prevent context-window timeouts.

- [`42ee0ef4`](https://github.com/JavRedstone/eyas/commit/42ee0ef4) — Fix event type naming, show activity field, reduce LLM input budget

### Preview bounding-box state

Fixed the live preview frame showing OBSERVING (orange box) instead of SUSPICIOUS (red box) immediately after a pickup event fires when no items were identified. The root cause was `record_pickup` requiring both `pickup_confirmed=True` AND a non-empty `picked_up_items` list; the fix seeds a placeholder so `draw_tracks()` renders the correct state.

- [`3e9cd8aa`](https://github.com/JavRedstone/eyas/commit/3e9cd8aa) — Fix preview showing OBSERVING when pickup event fires without identified items

### Multi-camera Q&A

Fixed Q&A in the "All Cameras" view silently ignoring every camera after the first. `answer_query` was not detecting the multi-cam case, so the 2400-char event budget was filled by one camera's events and the rest were dropped.

- [`19b8ca2d`](https://github.com/JavRedstone/eyas/commit/19b8ca2d) — Fix Q&A ignoring all-but-first camera in multi-cam session

### Video annotator cleanup

Removed the `_draw_zoom_inset` function that pasted a cropped close-up into the top-right corner of the annotated video.

- [`9114c2a9`](https://github.com/JavRedstone/eyas/commit/9114c2a9) — Remove zoom inset from annotated video

### Infrastructure and architecture

- [`42bab062`](https://github.com/JavRedstone/eyas/commit/42bab062) — Rename aisle1-4 clips to cam1-4
- [`a4ebe65a`](https://github.com/JavRedstone/eyas/commit/a4ebe65a) — Fix LLM GPU init, restore full session state on reload, aggregate All-chip summary
- [`9cbd87e7`](https://github.com/JavRedstone/eyas/commit/9cbd87e7) — Revert to CPU llama wheel and startup model load
- [`ceb955c5`](https://github.com/JavRedstone/eyas/commit/ceb955c5) — Add Eyas architecture diagram
- [`b72c29f7`](https://github.com/JavRedstone/eyas/commit/b72c29f7) — feat: duplicate video queue
- [`3780f3a1`](https://github.com/JavRedstone/eyas/commit/3780f3a1) — Fix multi-camera video loading
- [`1b26ca20`](https://github.com/JavRedstone/eyas/commit/1b26ca20) — Fix Korean labels for camera zone identifiers
- [`80dca02a`](https://github.com/JavRedstone/eyas/commit/80dca02a) — Fix '1 events' pluralization; remove Clip Library tab
- [`43c18800`](https://github.com/JavRedstone/eyas/commit/43c18800) — Add persistent SUSPICIOUS label and OBSERVING label to bounding boxes
- [`ffde9f48`](https://github.com/JavRedstone/eyas/commit/ffde9f48) — Add nanovllm-voxcpm TTS backend switcher for bare CUDA
- [`a8d98a77`](https://github.com/JavRedstone/eyas/commit/a8d98a77) — Remove nano-vllm-voxcpm from requirements to fix HF build
- [`70a45e28`](https://github.com/JavRedstone/eyas/commit/70a45e28) — Use pre-built llama-cpp-python CPU wheel to skip source compilation
- [`185d5265`](https://github.com/JavRedstone/eyas/commit/185d5265) — Fix requirements.txt to resolve VLM build error
- [`1bba082a`](https://github.com/JavRedstone/eyas/commit/1bba082a) — Default language to English; load LLM with GPU on ZeroGPU
- [`9e72fcd9`](https://github.com/JavRedstone/eyas/commit/9e72fcd9) — Fix LLM GPU via CUDA wheel; restore session on page reload

---

## Reasoning traces

Codex session logs (tool calls, reasoning steps, file edits) are stored in [`docs/../codex-traces/`](../codex-traces/). Each date folder contains a `trace.jsonl` with one JSON object per agent step.

| Session | Entries | Focus |
|---------|---------|-------|
| [2026-06-07](../codex-traces/2026-06-07/trace.jsonl) | 1709 | Initial pipeline, LLM integration, Gradio API backend |
| [2026-06-08](../codex-traces/2026-06-08/trace.jsonl) | 1273 | Multi-camera support, event structuring, frontend grid |
| [2026-06-09](../codex-traces/2026-06-09/trace.jsonl) | 1114 | Summary quality, LLM prompt tuning, Korean locale |
| [2026-06-10](../codex-traces/2026-06-10/trace.jsonl) | 173  | HF Spaces deployment fixes, GPU/CPU switching |
| [2026-06-12](../codex-traces/2026-06-12/trace.jsonl) | 182  | Session restore, All-view aggregation, architecture diagram |
| [2026-06-13](../codex-traces/2026-06-13/trace.jsonl) | 330  | Pickup detection accuracy, bounding box states, event UI |

---

For the structured event schema that flows between these stages, see [ARCHITECTURE.md — Event schema](../architecture/ARCHITECTURE.md#event-schema).
