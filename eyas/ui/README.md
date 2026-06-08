# ui

Gradio web application — the main operator-facing interface.

## Entry point

```bash
python ui/gradio_app.py
```

## Tabs

| Tab | Purpose |
|---|---|
| Upload | Upload a recorded clip and run the full visual pipeline |
| Live | Connect to a camera, record clips, and trigger analysis |
| Review | Browse the clip index, query the event log, generate alerts |

## Dependencies

Requires all pipeline modules (`object_detection`, `video_processing`, `event_structuring`, `llm`) to be importable.  
Heavy models (MiniCPM-V, GGUF LLM) are loaded lazily on first use.
