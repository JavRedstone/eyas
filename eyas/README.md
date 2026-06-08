# Eyas — Offline CCTV Security Assistant

Real-time retail loss-prevention pipeline: video → person tracking → VLM observation → event structuring → LLM reasoning → alerts.

## Pipeline

```
video / camera
  └─ object_detection/   YOLO11 + BotSORT → person tracks
       └─ video_processing/  MiniCPM-V 4.6 → structured observations
            └─ event_structuring/  heuristics → timestamped event log
                 └─ llm/           llama.cpp  → summaries, Q&A, alerts
                      └─ postprocessing/  translation + TTS
```

## Layout

| Folder | Purpose |
|---|---|
| `object_detection/` | YOLO person tracker, `Track` dataclass, crop helper |
| `video_processing/` | MiniCPM-V VLM, `PersonObservation`, frame buffer |
| `event_structuring/` | `EventStructurer`, zone definitions, event log serialisation |
| `llm/` | `Reasoner` (GGUF via llama.cpp), prompt templates, grammar |
| `postprocessing/` | Translation (llama.cpp) and TTS (VoxCPM2) |
| `streaming/` | Live camera capture with on-demand clip recording |
| `storage/` | Clip index — store, list, delete uploaded/recorded footage |
| `ui/` | Gradio web app |
| `utils/` | Shared helpers: device selection, video I/O, path resolution |
| `scripts/` | CLI entry points and batch utilities |
| `models/` | Local model weights (YOLO `.pt`, GGUF LLM) |
| `input/` | Sample input videos |
| `data/` | Static demo traces and reference data |
| `tests/` | Test suite — unit / module / e2e |

## Running

```bash
# Full visual pipeline on a video file
python scripts/run_visual_pipeline.py input/sample.mp4

# Gradio UI
python ui/gradio_app.py
```