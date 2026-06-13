# Eyas — Offline CCTV Security Assistant

Retail loss-prevention pipeline: video → person tracking → VLM observation → event structuring → LLM reasoning → alerts. Built for our teammate's family's store (Joy Convenience Store); sample clips (`aisle1`–`aisle4`) were filmed there.

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
| `utils/` | Shared helpers: device selection, video I/O, path resolution, overlay text |
| `scripts/` | CLI entry points and batch utilities |
| `models/` | Local model weights (YOLO `.pt`, GGUF LLM) |
| `assets/` | Bundled fonts for localized video overlay labels |
| `input/` | Sample input videos |
| `data/` | Static demo traces and reference data |
| `tests/` | Test suite — unit / module / e2e |

## Running

All commands run from the repo root.

```bash
# Full visual pipeline on a video file
python eyas/scripts/run_visual_pipeline.py eyas/input/sample.mp4

# Korean overlay labels on the annotated video
python eyas/scripts/run_visual_pipeline.py eyas/input/sample.mp4 --language ko

# Gradio API + React UI (http://localhost:7860)
python eyas/app.py
python eyas/app.py --lang ko
python eyas/app.py --port 7960

# Frontend hot-reload dev server (http://localhost:5173)
(cd eyas/ui/frontend && npm install)
(cd eyas/ui/frontend && npm run dev)
```
