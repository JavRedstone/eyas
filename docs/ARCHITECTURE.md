# Architecture — Offline CCTV Processing Pipeline

This document summarizes the modular, linear processing pipeline (left→right) that transforms raw video into structured events, applies language reasoning, and exposes multi-modal outputs via a Gradio app. It follows the diagram in image_846955.png.

## Overview
- Input: raw CCTV video
- Two parallel vision tracks: object counting and multimodal video understanding
- Event structuring: fuse detections into a time-mapped event log
- Language reasoning: local LLM via `llama.cpp` analyzes events and generates summaries/alerts
- Post-processing: translation and TTS for multi-lingual audio output
- UI: Gradio app that surfaces video, counts, logs, summaries, and audio

## Team assignments
These are the current owners for each pipeline area:
- **Joe**: Video Processing (MiniCPMV-4.6 / multimodal track)
- **Javier**: Language Reasoning (Nemotron models / `llama.cpp` runtime)
- **Hanhee**: Translation & transcription services (Cohere models)

Note: the names above match the labels used in the diagram (Joe, Javier, Hanhee) and indicate who is responsible for implementation and testing of the corresponding blocks.

## 1. Input Stage
- INPUT Video Footage: raw camera streams or uploaded clips (RTSP, MP4).
- Video is forked concurrently into the Object Detection track and the Video Processing track.

## 2. Processing & Analysis Tracks (parallel)
- Object Detection (Count)
  - Purpose: fast, robust counting / SKU-level or category-level detection for inventory and simple triggers.
  - Candidate models: YOLOv11 (full) or YOLOv8-tiny (lightweight).
  - Output: per-frame detections, per-zone counts, detection confidences.

- Video Processing (Multimodal)
  - Purpose: richer scene understanding, actions, and candidate-event extraction.
  - Candidate models: MiniCPMo-4.5 Omni (full) or MiniCPMV-4.6 1.3B for a lighter alternative.
  - Output: short-clip-level annotations (actions, object interactions, timestamps).

## 3. Event Structuring
- The Event Structuring node ingests detection streams and clip annotations.
- Responsibilities:
  - Map detections into zones (entrance, counter, back door, aisles).
  - Group temporally adjacent detections into events (entry, dwell, pick-up, concealment, exit).
  - Attach metadata: camera id, zone, bounding boxes, confidence, clip pointers.
- Output: a time-ordered structured event log (JSON/SQLite) used by downstream components.

## 4. Language Reasoning (local LLM via llama.cpp)
- Purpose: convert structured events into natural-language summaries, alerts, and QA responses.
- Runtime: runs locally using `llama.cpp` bindings.
  - Candidate models: Nemotron 3 Nano 4B for lightweight local reasoning, or Nemotron 3 Nano 30B-A3B for stronger reasoning where hardware allows.
- Typical prompts/functions:
  - Summarize a time window ("overnight summary").
  - Generate an alert description from a suspicious event.
  - Answer direct queries about the event log.

## 5. Post-Processing & Enrichment
- Alert Summary
  - Receives LLM output and packages short, action-oriented alerts.
  - Adds metadata links to the underlying clips and timestamps for fast review.

- Translation
  - Optional localization block for multilingual deployments.
  - Suggested models: Cohere-transcribe-03-2026 or Cohere Tiny Aya for lighter load.
  - Use-case: translate alerts and summaries before TTS or UI display.

- Voice Output (TTS)
  - Converts translated text to audio for spoken alerts.
  - Suggested model: VoxCPM2 TTS (local or hosted depending on constraints).

## 6. User Interface (Gradio App)
- The central user-facing hub. Key responsibilities:
  - Ingest input video or sample clips.
  - Display object counts and per-zone metrics from the Object Detection track.
  - Show the Event Structuring log with quick clip previews and metadata.
  - Surface LLM-generated summaries, QA answers, and alert details.
  - Play translated audio from the Voice Output stage.
- Design notes:
  - Expose clip-level "jump to video" links for human review.
  - Show confidence scores and a short explanation for each alert to support human triage.

## Integration notes & trade-offs
- Local-first vs cloud:
  - `llama.cpp` and tiny models enable fully offline deployments (privacy-friendly, eligible for Off the Grid bonus).
  - Larger models (Nemotron 30B) or cloud translation/tts may require more resources or hosted infra.
- Robustness:
  - Counting/YOLO track is optimized for speed and simpler invariants; multimodal track handles nuanced events.
  - Event structuring heuristics are critical: tune zone definitions, time thresholds, and merging rules.
- Accuracy:
  - Accuracy depends on camera placement, lighting, occlusion, and training data for the chosen models.
  - Multi-camera coverage and integration with POS/inventory systems dramatically reduce false positives.

## Privacy & safety
- Treat LLM alerts as leads for human review — do not automate punitive actions.
- Prefer anonymized logs (no persistent face IDs) unless explicitly required and compliant.
- Keep retention policies and audit logs for alerts and reviewer actions.

## Deployment checklist (quick)
- Camera feeds or sample clips available (RTSP or MP4).
- Chosen object-detection and video models downloaded and verified.
- Local `llama.cpp` runtime installed and tested with selected Nemotron model.
- Gradio app scaffolded with endpoints to read the event log and play clips.
- Minimal monitoring: alert queue, review UI, and logging/audit trails.

---

If you'd like, I can link this file from `docs/HACKATHON.md` and/or add a small diagram snippet and quick-start run commands for a prototype environment.