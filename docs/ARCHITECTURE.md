# Architecture — Eyas Pipeline

Linear processing pipeline: raw video → tracks → observations → events → reasoning → UI.

## Pipeline overview

```
Input video (MP4 / camera)
  │
  ├─ object_detection/    YOLO11n + BotSORT
  │    └─ Track[]         per-frame person tracks with crop
  │
  ├─ video_processing/    MiniCPM-V 4.6 (1.3B VLM)
  │    └─ PersonObservation[]  description, activity, held_objects, pickup_confirmed
  │
  ├─ event_structuring/   heuristic event builder
  │    └─ Event[]         timestamped, zone-tagged, typed events (pickup, loitering, …)
  │
  ├─ llm/                 Nemotron 3 Nano 4B (GGUF via llama.cpp)
  │    └─ LLMResult       summary, flags, risk_level, suspicious_clips
  │
  └─ postprocessing/      optional enrichment
       ├─ translation     TinyAya GGUF → Korean (or other locales)
       └─ tts             VoxCPM2 → spoken audio brief
```

The pipeline runs in a background thread; Gradio streams progress updates to the React frontend via a generator endpoint.

## Components

### object_detection

- **Model**: YOLO11n (`yolo11n.pt`) with BotSORT tracking
- **Input**: BGR video frames
- **Output**: `Track[]` — track_id, label, confidence, bbox
- Crops around each bounding box are passed to the VLM

### video_processing

- **Model**: MiniCPM-V 4.6 Transformers (default) or GGUF via llama-cpp-python
- **Input**: List of person crop frames per track
- **Output**: `PersonObservation` — structured JSON parsed from VLM response
- Frames are sub-sampled to at most `k` before the VLM call
- `PersonObservation.pickup_confirmed` drives the `pickup` event kind

### event_structuring

- Maintains a per-track observation buffer with configurable evidence window
- Emits an `Event` when a track exits or the buffer reaches the flush threshold
- Zone assignment uses configurable polygons (`--zone NAME:KIND:X1,Y1,X2,Y2`)
- Produced events: `pickup`, `loitering`, `observation`, `intrusion`, `suspicious`

### llm

- **Model**: Nemotron 3 Nano 4B GGUF, Q4_K_M quantization
- **Runtime**: `llama-cpp-python` (CPU build on HF Spaces; Metal on Apple Silicon)
- Functions: `summarize_events()`, `answer_query()`, `generate_alert()`
- Context window: 4096 tokens; constrained grammar for structured JSON output

### postprocessing

- **Translation**: TinyAya GGUF via llama-cpp-python; cached; retries once on invalid output
- **TTS**: VoxCPM2 (requires CUDA); streams `(sample_rate, audio_chunk)` pairs
- Both are optional — pipeline runs without them when models are unavailable

### ui

- **Backend**: Gradio Blocks with all UI components hidden; exposes API endpoints only
- **Frontend**: React + Vite SPA served as static files from `eyas/ui/dist/`
- **Communication**: `@gradio/client` JS SDK via `/gradio_api`
- Resizable split layout: video + footage controls on the left, analysis tabs on the right
- See [ui/README.md](../eyas/ui/README.md) for the full tab breakdown

## Data flow (single pipeline run)

1. React calls `/run_pipeline` with the video path
2. Gradio streams JSON update objects as the pipeline progresses
3. React updates pipeline step state, event list, and video src incrementally
4. On completion, the final update includes `annotated_video_path`, `summary`, and `output_dir`
5. Subsequent tab actions (Q&A, audio, clip load) call individual Gradio endpoints

## Multi-camera session

The frontend maintains a session layer on top of individual pipeline runs. Multiple clips (one per camera angle) can be queued and processed sequentially. Events from each clip are merged into a unified session event list tagged with their source zone. After all clips complete, a `summarize_session` endpoint aggregates the cross-camera event log into a combined summary with per-camera breakdowns. The Summary & Alerts tab renders both the total summary and the per-camera detail sections.

## Video encoding

All `VideoWriter` instances use the `avc1` (H.264) fourcc — required for browser-compatible MP4 playback. The default `mp4v` codec produces FMP4 which most browsers do not support inline.

## Deployment

See the root [README.md](../README.md) for Docker and HF Spaces deployment details.
