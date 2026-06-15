# Architecture — Eyas Pipeline

Linear processing pipeline: raw video → tracks → observations → events → reasoning → UI.

## Pipeline overview

<p align="center">
  <img src="../assets/eyas-architecture-diagram.png" alt="Eyas architecture diagram" width="900" />
</p>

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
- See [ui/README.md](../../eyas/ui/README.md) for the full tab breakdown

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

## Event schema

A structured event as produced by `event_structuring/` and consumed by `llm/`:

```json
{
  "track_id": 2,
  "timestamp": 5.84,
  "confirmation_timestamp": 5.84,
  "description": "Two individuals in a convenience store, one in dark clothing bending over a shelf...",
  "activity": "The person in dark clothing bends down to interact with a shelf, possibly picking up or examining an item.",
  "held_objects": [],
  "pickup_confirmed": true,
  "picked_up_items": [],
  "summary": "Person 2 observed at counter. Pickup confirmed; item unidentified.",
  "zone": "counter",
  "backend": "minicpmv",
  "raw_observation": "{\"description\": \"...\", \"pickup_confirmed\": false, ...}",
  "bbox": [1182, 235, 1476, 912],
  "confidence": 0.857,
  "source_video": "20260608_130000_counter.mp4",
  "source_clip_id": "20260614_121209",
  "source_event_index": 5
}
```

| Field | Notes |
|-------|-------|
| `pickup_confirmed` | Set by heuristic structurer. Can be `true` even when `raw_observation` shows `false` — the structurer overrides the VLM's conservative judgment based on activity keywords and confidence. |
| `picked_up_items: []` | The "item unidentified" path — pickup confirmed but the VLM could not name the object. Reasoner emits `Pickup: YES (item unidentified)`. |
| `summary` | Human-readable per-track summary generated by the event structurer after all observations are merged. |
| `raw_observation` | Verbatim VLM JSON before heuristic overrides, stored for auditability. |
| `zone` | Derived from the filename convention (`*_counter.mp4` → `counter`). No manual annotation required. |
| `source_video` / `source_event_index` | Full traceability back to the original video file and session event index. |

## Deployment

See the root [README.md](../../README.md) for Docker and HF Spaces deployment details.
