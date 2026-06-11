# ui

Gradio API backend + React frontend for the Eyas operator interface.

## Architecture

Gradio runs as a **pure API backend** — all its UI components are hidden. The React SPA (built by Vite) is served as static files from `eyas/ui/dist/` and communicates with Gradio via the `@gradio/client` JS SDK.

## Entry point

```bash
python app.py                 # English, port 7860
python app.py --lang ko       # Korean
python app.py --port 7960     # custom port
```

## Frontend development

```bash
cd eyas/ui/frontend
npm install
npm run dev      # http://localhost:5173 — proxies /gradio_api → 7860
npm run build    # output → eyas/ui/dist/
```

The Vite dev server proxies all `/gradio_api/*` requests to the running Gradio backend, so both hot-reload dev and production mode use the same API surface.

## Tabs

| Tab | Purpose |
|---|---|
| **Event Timeline** | Scatter chart + event table; click row or dot to seek the annotated video; "clip" button loads a 6-second clip into the left panel |
| **Summary & Alerts** | Risk gauge (radial bar), flag-type pie chart, overnight summary text, suspicious clip list |
| **Ask Footage** | Chat interface — Q&A about the event log via the on-device LLM |
| **Detection Metrics** | Per-zone detection bar chart and event-count timeline |
| **Audio Report** | Generates a spoken brief via VoxCPM2 TTS; shows progress phases |
| **Clip Library** | Browse stored clips; preview, load for analysis, or delete |
| **Settings** | Language selector (English / 한국어); saves to `preferences.json` and hot-swaps at runtime |

## Language

Default language is English. Switch to Korean via:

- **Settings** tab → select 한국어 → Save (no restart needed)
- `preferences.json`: `"language": "ko"`
- CLI flag: `--lang ko`

String catalogs live in [`locale.py`](locale.py) (`en` / `ko`). When Korean is active:

- Event table headers, event types, zones, and known activities come from the locale catalog
- Freeform VLM activity text is translated live via TinyAya as events arrive
- Annotated video overlays are rendered with the bundled Noto Sans CJK font
- LLM summary, Q&A replies, and TTS input are post-translated before display/playback

## Key files

| File | Purpose |
|---|---|
| [`gradio_app.py`](gradio_app.py) | All Gradio API endpoints as closures |
| [`locale.py`](locale.py) | `Strings` class, `LANGUAGE_LABELS`, `localize_text`, `format_event_row` |
| [`frontend/src/App.jsx`](frontend/src/App.jsx) | Root component — resizable split layout, pipeline state, video refs |
| [`frontend/src/components/`](frontend/src/components/) | Header, Sidebar, AnalysisPanel, TabNav |
| [`frontend/src/components/tabs/`](frontend/src/components/tabs/) | One file per tab |
| [`frontend/tailwind.config.js`](frontend/tailwind.config.js) | Eyas falcon color theme |

## Dependencies

All pipeline modules (`object_detection`, `video_processing`, `event_structuring`, `llm`) must be importable. Heavy models load lazily on first use.
