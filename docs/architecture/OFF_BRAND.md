# Off-Brand Frontend — React SPA over Gradio API

Eyas is a Gradio Space that contains no visible Gradio components. There is no `gr.Video()`, no `gr.Chatbot()`, no `gr.Dataframe()` — none of the standard building blocks that make up 99% of Gradio Spaces. Instead, Gradio runs as a **pure HTTP/WebSocket API backend** with every native UI component hidden, and a fully custom React + Vite SPA is served in front of it.

This is unusual. The two normal paths for customizing a Gradio Space are:

1. **Use Gradio components** — drop in `gr.Video`, `gr.Chatbot`, `gr.Plot`, arrange them with `gr.Row`/`gr.Column`, and accept the look and behavior Gradio gives you.
2. **Inject HTML/CSS/JS** — use `gr.HTML()` for inline markup, `css=` on `gr.Blocks` for style overrides, `js=` for boot scripts, or `head=` to load external libraries. This gets you further, but you're still writing flat strings of HTML inside Python, event wiring is done by patching the DOM after Gradio finishes rendering, and you're fighting Gradio's own CSS and component lifecycle the whole way.

Eyas does neither. Gradio is treated as infrastructure — it handles routing, file serving, streaming, and HF Spaces integration — but it owns zero pixels of the UI.

---

## Why not raw Gradio components?

Gradio's component library is great for rapid ML demos. But the Eyas interface has requirements that simply don't map onto it:

- **Resizable split layout** — video left, tabs right, with a drag handle the user can move
- **Multi-camera grid** — 2×2 synchronized feed grid with per-clip highlight when an event is clicked
- **Live video seek** — clicking a row in the event table seeks every visible video element simultaneously
- **Scatter chart + event table cross-linked** — clicking a chart dot selects the table row; clicking a table row highlights the dot
- **Custom MUI theme** — navy/yellow dark mode and warm-yellow/blue light mode, a consistent design token system across every component
- **Framer Motion transitions** — splash screen to app with an animated fade-in
- **Korean hot-swap** — language switch propagates through every string and re-localizes event data without a page reload

Gradio components aren't designed to be composed into custom layouts like this. Rather than fighting the library with extensive CSS overrides and `gr.HTML()` injections, we replaced the view layer entirely and kept only the API routing.

---

## How it works

```
Browser
  │
  │  GET /            → index.html (served by FastAPI at app startup)
  │  GET /ui/*        → Vite bundle assets (JS, CSS, fonts)
  │  POST/WS /gradio_api/*  → Gradio API endpoints
  │
FastAPI (eyas/app.py)
  │
  ├─ StaticFiles("/ui", dir="eyas/ui/dist")
  ├─ GET "/" → eyas/ui/dist/index.html
  └─ Gradio block (all components hidden, exposes /gradio_api/*)
```

### Server side (`eyas/app.py`)

```python
_STATIC_DIR = Path(__file__).parent / "ui" / "dist"

# Mount the Vite bundle
app.app.mount("/ui", StaticFiles(directory=str(_STATIC_DIR)), name="ui-static")

# SPA fallback — all non-asset routes return index.html
@app.app.get("/")
async def spa_root():
    return FileResponse(_INDEX_PATH)
```

The Gradio `Blocks` instance has no visible components. It is used only to register Python functions as callable API endpoints under `/gradio_api/`. Gradio handles the HTTP routing, streaming, file serving, and WebSocket plumbing; the React app calls those endpoints directly.

### Client side (`backend.js`)

```js
export const GRADIO_BACKEND_URL =
  import.meta.env.VITE_GRADIO_BACKEND_URL ||
  (import.meta.env.DEV ? 'http://127.0.0.1:7860' : window.location.origin)
```

- **Development** — Vite dev server runs on port 5173 and proxies all `/gradio_api/*` requests to `localhost:7860`. The React hot-reload loop and the Python pipeline stay in sync with no CORS configuration.
- **Production / HF Spaces** — the bundle is served from the same origin as Gradio, so `window.location.origin` is the correct base URL for API calls.

### Connecting to Gradio

`App.jsx` connects on mount using the `@gradio/client` SDK:

```js
Client.connect(GRADIO_BACKEND_URL)
  .then(c => { setClient(c); pollSplash(c); loadSamples(c) })
```

Every pipeline call goes through this client. Streaming calls use `client.submit()` which returns an async iterator of server-sent events:

```js
const sub = client.submit('/run_pipeline', { video_path: gradioPath })
for await (const msg of sub) {
  if (msg.type !== 'data') continue
  const u = msg.data[0]
  // update events, progress, video src, etc.
}
```

Gradio serializes each `yield` from the Python generator as a JSON payload; the frontend consumes them incrementally so the event list, progress bar, and video preview update in real time without waiting for the pipeline to finish.

---

## Frontend structure

```
eyas/ui/frontend/
├── vite.config.js           base: '/ui/', outDir: '../dist'
├── package.json
└── src/
    ├── main.jsx             ReactDOM.createRoot → <App />
    ├── App.jsx              Root: all pipeline state, video refs, layout
    ├── backend.js           GRADIO_BACKEND_URL, gradioFileUrl, resolveGradioFile
    ├── theme.js             MUI dark/light theme (Eyas falcon palette)
    ├── i18n.js              String catalog: English + 한국어
    ├── display.js           Display helpers
    ├── components/
    │   ├── Header.jsx       Logo, language toggle (EN/한), dark/light toggle
    │   ├── Sidebar.jsx      Queue list, sample picker, file upload, session controls
    │   ├── AnalysisPanel.jsx  Step progress, analyze / stop buttons
    │   ├── ClipViewSelector.jsx  All / per-clip chip strip
    │   ├── SidebarTabs.jsx  Icon-only vertical tab strip (Lucide icons)
    │   └── Splash.jsx       Model loading overlay with per-step progress
    └── components/tabs/
        ├── EventTimeline.jsx   Recharts scatter chart + MUI table; video seek on click
        ├── SummaryAlerts.jsx   Risk gauge, flag pie, per-cam narratives
        ├── AskFootage.jsx      Chat Q&A via /ask_footage Gradio endpoint
        ├── DetectionMetrics.jsx  Per-zone bar chart, event frequency chart
        ├── AudioReport.jsx     TTS generation with streaming phase labels
        └── SettingsTab.jsx     Language selector
```

### Key design choices

**MUI as the component system** — Material UI v6 provides the base components (Box, Paper, Typography, Chip, Table, etc.) themed with a fully custom `createTheme` call. No Gradio CSS leaks in. The Eyas palette:
- Dark: yellow `#f7d046` primary on navy `#0b1929` background
- Light: blue `#1565C0` primary on warm yellow `#fef9e7` background

**Framer Motion for the splash** — The `Splash` component uses `AnimatePresence` + `motion.div` for the fade from loading screen to the main app. Without this, the app would flash from blank to loaded.

**`display: none` tab switching** — Instead of React Router or unmounting, inactive tabs stay mounted with `display: none`. This preserves chart zoom state, video playback position, and chat history across tab switches without re-rendering.

**Sync-locked grid playback** — The multi-camera grid uses `useRef` arrays for video elements and a timed lock (`syncLockRef`) to prevent seek events from echoing. When the user seeks camera A, the handler programmatically seeks cameras B/C/D; without the lock, those programmatic seeks would fire their own `onSeeked` events and loop.

**Resizable split** — The drag handle between queue/analysis and the footage preview is a pure mouse event handler that updates a `topColPct` percentage state. MUI `Box` uses `style={{ flex: topColPct }}` (not `sx`) so it bypasses MUI's CSS-in-JS cache — critical for smooth dragging.

---

## Build and deploy

### Development

```bash
# Terminal 1 — Python backend
python eyas/app.py

# Terminal 2 — Vite dev server with HMR
cd eyas/ui/frontend && npm run dev
# → http://localhost:5173
```

Vite's dev proxy routes `/gradio_api/*` to `localhost:7860`, so the frontend sees one consistent API surface in both dev and prod.

### Production build

```bash
cd eyas/ui/frontend && npm run build
# Output → eyas/ui/dist/
```

The built `dist/` directory is committed to the repo and shipped as-is. HF Spaces starts `eyas/app.py` via `app_file: eyas/app.py` in the README frontmatter; FastAPI then serves the pre-built bundle at `/`.

### HF Spaces: why the bundle is committed

HF Spaces does not run `npm install` or `npm run build` at deploy time — it only installs Python dependencies from `requirements.txt`. The built Vite output (`eyas/ui/dist/`) must already exist in the repo. This is the main operational difference from a standard Vite deployment where the CI pipeline builds the frontend.

---

## What Gradio still owns

Despite the custom frontend, Gradio handles several things that would be tedious to replicate:

- **File upload and serving** — `client.upload()` + `/gradio_api/file=` URLs give browser-accessible paths for any file the Python pipeline writes to disk.
- **Streaming** — `yield`-based Python generators automatically become server-sent event streams consumed by `client.submit()`.
- **State management** — Gradio `State` components hold per-session data server-side without needing a separate database or session store.
- **HF Spaces runtime** — The Space's OAuth, GPU allocation, and ZeroGPU burst are all tied to the Gradio app instance. Replacing Gradio entirely would lose these platform integrations.
