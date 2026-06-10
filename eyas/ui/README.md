# ui

Gradio web application — the main operator-facing interface.

## Entry point

```bash
python app.py
python app.py --lang ko
```

## Language

UI language is English by default. Set Korean via:

- **Settings** tab → Language → Save → restart the server
- `preferences.json`: `"language": "ko"`
- CLI: `python app.py --lang ko`

String catalogs live in [`locale.py`](locale.py) (`en` / `ko`).

When language is Korean, annotated video overlay labels (person descriptions, activities, pickup/holding text) are translated and rendered with the bundled Noto font via [`utils/overlay_text.py`](../utils/overlay_text.py).

## Tabs

| Tab | Purpose |
|---|---|
| Upload | Upload a recorded clip and run the full visual pipeline |
| Live | Connect to a camera, record clips, and trigger analysis |
| Review | Browse the clip index, query the event log, generate alerts |

## Dependencies

Requires all pipeline modules (`object_detection`, `video_processing`, `event_structuring`, `llm`) to be importable.  
Heavy models (MiniCPM-V, GGUF LLM) are loaded lazily on first use.
