# frontend

React + Vite SPA for the Eyas UI. Gradio acts as a pure API backend; this app is the only user-facing interface.

## Stack

- **React 18** — component tree
- **Vite 8** — build tool and dev server
- **MUI (Material UI v6)** — theming, layout, and all UI components; Eyas falcon dark theme via `src/theme.js`
- **Framer Motion** — page and panel animations
- **Recharts** — event scatter chart, bar charts, radial gauge, pie chart
- **Lucide React** — icons
- **@gradio/client** — connects to the Gradio API at `/gradio_api`

## Dev

```bash
npm install
npm run dev      # http://localhost:5173
```

Vite proxies `/gradio_api/*` to `http://localhost:7860` (the running Gradio backend). Start Gradio first:

```bash
# from eyas/
python app.py
```

## Build

```bash
npm run build    # outputs to ../dist/ (eyas/ui/dist/)
```

Gradio serves `dist/` as static files in production.

## Theme

Defined in [`src/theme.js`](src/theme.js) as a MUI `createTheme()` — inspired by the Peregrine falcon (*Eyas*):

| MUI palette key | Hex | Source |
|---|---|---|
| `background.default` | `#0e2946` | Dark slate blue — back plumage |
| `background.paper` | `#1f2833` | Charcoal — head stripes |
| `primary.main` | `#f7d046` | Bright yellow — cere and talons |
| `text.primary` | `#e5e1d8` | Soft cream — underbelly |
| `text.secondary` | `#7a8ea8` | Blue-grey — secondary text |
| `divider` | `#2e4060` | Border / rule color |

## Component tree

```
App.jsx                    Root — resizable split layout, all pipeline state
  Header.jsx               App bar — title and active language indicator
  Sidebar.jsx              Footage controls — upload zone, sample picker
  AnalysisPanel.jsx        Run pipeline button, step progress, status
  TabNav.jsx               Tab bar
  tabs/
    EventTimeline.jsx      Scatter chart + event table + clip loader
    SummaryAlerts.jsx      Risk gauge, flag pie, summary text
    AskFootage.jsx         LLM chat interface
    DetectionMetrics.jsx   Zone bar chart + event density line chart
    AudioReport.jsx        TTS generation with progress phases
    ClipLibrary.jsx        Stored clip browser
    SettingsTab.jsx        Language selector
```
