# Eyas — Prototype CCTV processing project

This folder contains a modular prototype scaffold for the Offline CCTV Security Assistant described in `docs/PROJECT_IDEA.md` and `docs/ARCHITECTURE.md`.

Structure
- `input/` — video ingest helpers and example clips
- `object_detection/` — YOLO-based counting detector
- `video_processing/` — multimodal video understanding and clip annotation
- `event_structuring/` — heuristics to convert detections into events
- `llm/` — local LLM prompts and reasoning via `llama.cpp`
- `postprocessing/` — translation and TTS wrappers
- `ui/` — Gradio app and UI components
- `models/` — local model artifacts
- `scripts/` — utility scripts (convert, split, annotate)
- `data/` — sample or anonymized traces used for demo
- `tests/` — simple unit/integration checks

Quick notes
- This is a scaffold: files contain minimal placeholder code and TODOs.
- To add a runnable prototype, implement the detector and a small Gradio UI in `ui/`.

Contact
- See `docs/ARCHITECTURE.md` for ownership mapping and model choices.