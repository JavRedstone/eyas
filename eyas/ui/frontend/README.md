# frontend

React + Vite SPA for the Eyas UI. Gradio acts as a pure API backend; this app is the only user-facing interface.

## Stack

- **React 18** — component tree
- **Vite 8** — build tool and dev server
- **MUI (Material UI v6)** — theming, layout, and all UI components; dark/light Eyas falcon theme in `src/theme.js`
- **Framer Motion** — page and panel animations
- **Recharts** — event scatter chart, bar charts, radial gauge, pie chart
- **Lucide React** — icons
- **@gradio/client** — connects directly to the Gradio backend

## Dev

Start Gradio first, then the dev server (all from repo root):

```bash
python eyas/app.py                               # http://localhost:7860
(cd eyas/ui/frontend && npm install)
(cd eyas/ui/frontend && npm run dev)            # http://localhost:5173
```

During development the frontend connects to `http://127.0.0.1:7860`. Override
the backend URL when needed:

```bash
VITE_GRADIO_BACKEND_URL=http://127.0.0.1:7861 npm run dev
```

Production builds connect to the same origin that serves the frontend.

## Build

```bash
(cd eyas/ui/frontend && npm run build)    # outputs to eyas/ui/dist/
```

Gradio serves `dist/` as static files in production.

## Theme

Defined in [`src/theme.js`](src/theme.js) as a `createEyasTheme(mode)` function — two modes, toggle in the header:

| | Dark | Light |
|---|---|---|
| `background.default` | `#0b1929` navy | `#fef9e7` warm yellow |
| `background.paper` | `#0f2338` slate | `#ffffff` white |
| `primary.main` | `#f7d046` yellow | `#1565C0` blue |
| `secondary.main` | `#4b9eff` blue | `#d4a017` golden |
| `text.primary` | `#e5e1d8` cream | `#0d1b2a` navy |
| `divider` | `#1a3352` | `#dfc85e` |

Mode preference is saved to `localStorage` and respected on reload.

## Component tree

```
App.jsx                    Root — theme provider, resizable split layout, all pipeline state
  Header.jsx               App bar — title, EN/한 language toggle, dark/light mode toggle
  Sidebar.jsx              Footage controls — upload zone, sample picker
  AnalysisPanel.jsx        Run pipeline button, step progress, status
  TabNav.jsx               Tab bar (MUI Tabs)
  tabs/
    EventTimeline.jsx      Scatter chart + event table + clip loader
    SummaryAlerts.jsx      Risk gauge, flag pie, summary text
    AskFootage.jsx         LLM chat interface
    DetectionMetrics.jsx   Zone bar chart + event density line chart
    AudioReport.jsx        TTS generation with progress phases
    ClipLibrary.jsx        Stored clip browser
    SettingsTab.jsx        Language selector with save confirmation
```
