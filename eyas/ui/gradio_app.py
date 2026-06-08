"""Gradio UI for Eyas — AI Security Camera Agent.

Theme is selected at startup (via preferences.json / CLI) and baked into
the Gradio theme object.  No runtime CSS class-toggling; restart to change.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

import gradio as gr
from gradio.themes.base import Base
from gradio.themes.utils import colors, fonts, sizes

from storage import manager as storage
from streaming.capture import default_capture as _stream

# ---------------------------------------------------------------------------
# Palette definitions
# ---------------------------------------------------------------------------

_DARK: Dict[str, Dict] = {
    "night": dict(
        bg="#0a0e17", panel="#111827", surface="#1f2937", border="#2d3748",
        accent="#10b981", accent_hover="#059669", text="#f1f5f9",
        muted="#9ca3af", danger="#f87171", label="#9ca3af", hue=colors.emerald,
    ),
    "amber": dict(
        bg="#0c0900", panel="#1a1200", surface="#261b00", border="#3d2a00",
        accent="#f59e0b", accent_hover="#d97706", text="#fef3c7",
        muted="#d97706", danger="#ef4444", label="#d97706", hue=colors.amber,
    ),
    "cyber": dict(
        bg="#06000f", panel="#0f0020", surface="#1a0035", border="#2d0060",
        accent="#a855f7", accent_hover="#9333ea", text="#f0e6ff",
        muted="#a78bfa", danger="#f43f5e", label="#a78bfa", hue=colors.purple,
    ),
    "sentinel": dict(
        bg="#0f1923", panel="#1a2535", surface="#243040", border="#2e3f55",
        accent="#3b82f6", accent_hover="#2563eb", text="#f1f5f9",
        muted="#94a3b8", danger="#f87171", label="#94a3b8", hue=colors.blue,
    ),
}

_LIGHT: Dict[str, Dict] = {
    "night": dict(
        bg="#f0f4f8", panel="#ffffff", surface="#f8fafc", border="#e2e8f0",
        accent="#059669", accent_hover="#047857", text="#0f172a",
        muted="#475569", danger="#dc2626", label="#475569", hue=colors.emerald,
    ),
    "amber": dict(
        bg="#fffbf0", panel="#ffffff", surface="#fef9f0", border="#fde68a",
        accent="#d97706", accent_hover="#b45309", text="#1c0a00",
        muted="#92400e", danger="#dc2626", label="#92400e", hue=colors.amber,
    ),
    "cyber": dict(
        bg="#f5f0ff", panel="#ffffff", surface="#faf5ff", border="#e9d5ff",
        accent="#9333ea", accent_hover="#7c3aed", text="#1e0540",
        muted="#6d28d9", danger="#dc2626", label="#6d28d9", hue=colors.purple,
    ),
    "sentinel": dict(
        bg="#eff6ff", panel="#ffffff", surface="#f0f9ff", border="#bfdbfe",
        accent="#2563eb", accent_hover="#1d4ed8", text="#0f1923",
        muted="#1e40af", danger="#dc2626", label="#1e40af", hue=colors.blue,
    ),
}

_COLOR_NAMES = {
    "night": "Night Vision",
    "amber": "Amber CRT",
    "cyber": "Cyberpunk",
    "sentinel": "Sentinel",
}
_COLOR_KEY = {v: k for k, v in _COLOR_NAMES.items()}  # "Night Vision" -> "night", etc.


# ---------------------------------------------------------------------------
# Advanced palettes — sourced from designs/*/DESIGN.md (awesome-design-md)
# ---------------------------------------------------------------------------

_ADVANCED: Dict[str, Dict] = {
    "voltagent": dict(
        bg="#101010", panel="#1a1a1a", surface="#222222", border="#3d3a39",
        accent="#00d992", accent_hover="#10b981", text="#f2f2f2",
        muted="#8b949e", danger="#ef4444", label="#bdbdbd", hue=colors.emerald,
    ),
    "xai": dict(
        bg="#0a0a0a", panel="#191919", surface="#1a1c20", border="#212327",
        accent="#ff7a17", accent_hover="#e06010", text="#ffffff",
        muted="#7d8187", danger="#ef4444", label="#dadbdf", hue=colors.orange,
    ),
    "warp": dict(
        bg="#2b2622", panel="#383330", surface="#3f3a36", border="#4a453f",
        accent="#f7f5f0", accent_hover="#ffffff", text="#f7f5f0",
        muted="#aea69c", danger="#ef4444", label="#c9c0ad", hue=colors.amber,
    ),
    "linear": dict(
        bg="#010102", panel="#0f1011", surface="#141516", border="#23252a",
        accent="#5e6ad2", accent_hover="#828fff", text="#f7f8f8",
        muted="#8a8f98", danger="#ef4444", label="#d0d6e0", hue=colors.indigo,
    ),
    "sentry": dict(
        bg="#150f23", panel="#1f1633", surface="#2a1f40", border="#362d59",
        accent="#c2ef4e", accent_hover="#a8d435", text="#ffffff",
        muted="#bdb8c0", danger="#fa7faa", label="#bdb8c0", hue=colors.green,
    ),
    "stripe": dict(
        bg="#0d253d", panel="#1c1e54", surface="#21235a", border="#2e3560",
        accent="#533afd", accent_hover="#4434d4", text="#ffffff",
        muted="#64748d", danger="#ea2261", label="#a0b4c8", hue=colors.indigo,
    ),
    "supabase": dict(
        bg="#1c1c1c", panel="#202020", surface="#242424", border="#333333",
        accent="#3ecf8e", accent_hover="#24b47e", text="#ffffff",
        muted="#707070", danger="#ef4444", label="#9a9a9a", hue=colors.emerald,
    ),
    "vercel": dict(
        bg="#000000", panel="#111111", surface="#1a1a1a", border="#333333",
        accent="#0070f3", accent_hover="#0761d1", text="#ffffff",
        muted="#888888", danger="#ee0000", label="#a1a1a1", hue=colors.blue,
    ),
    "cursor": dict(
        bg="#f7f7f4", panel="#ffffff", surface="#f0efe8", border="#e6e5e0",
        accent="#f54e00", accent_hover="#d04200", text="#26251e",
        muted="#807d72", danger="#cf2d56", label="#5a5852", hue=colors.orange,
    ),
    "runway": dict(
        bg="#000000", panel="#1a1a1a", surface="#030303", border="#27272a",
        accent="#ffffff", accent_hover="#e5e5e5", text="#ffffff",
        muted="#767d88", danger="#ef4444", label="#a7a7a7", hue=colors.gray,
    ),
}

_ADVANCED_NAMES: Dict[str, str] = {
    "voltagent": "VoltAgent",
    "xai":       "xAI",
    "warp":      "Warp",
    "linear":    "Linear",
    "sentry":    "Sentry",
    "stripe":    "Stripe",
    "supabase":  "Supabase",
    "vercel":    "Vercel",
    "cursor":    "Cursor",
    "runway":    "Runway",
}
_ADVANCED_KEY: Dict[str, str] = {v: k for k, v in _ADVANCED_NAMES.items()}


def _theme_label(color: str, dark: bool) -> str:
    return f"{_COLOR_NAMES[color]} · {'Dark' if dark else 'Light'}"


# ---------------------------------------------------------------------------
# CSS — palette values baked in at startup via _build_css(palette)
# ---------------------------------------------------------------------------

_STRUCTURAL_CSS = """
footer { display: none !important; }
.app-title, .main-header h1, h1.title,
.gradio-container > .main > .wrap > .prose h1:first-child { display: none !important; }

/* Header: transparent wrappers */
#eyas-header, #eyas-header .block, #eyas-header .form {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}
#theme-col, #theme-col .block, #theme-col .form {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    display: flex !important;
    justify-content: flex-end !important;
    align-items: flex-start !important;
}

/* Theme badge */
.eyas-theme-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: var(--_surface);
    border: 1px solid var(--_border);
    border-radius: 6px;
    padding: 5px 11px;
    font-size: 0.72rem;
    color: var(--_muted);
    letter-spacing: 0.03em;
    white-space: nowrap;
    line-height: 1.4;
}
.eyas-theme-badge strong {
    color: var(--_text);
    font-weight: 600;
}

/* Header content */
.eyas-title-row { display: flex; align-items: center; gap: 10px; margin-bottom: 5px; }
.eyas-title    { color: var(--_accent); font-family: var(--font-mono); font-size: 1.35rem; font-weight: 700; letter-spacing: .1em; }
.eyas-tagline  { color: var(--_text);   font-family: var(--font-mono); font-size: .85rem; letter-spacing: .06em; margin-bottom: 4px; }
.eyas-subtitle { color: var(--_muted);  font-size: .82rem; margin: 0 0 12px; }
.eyas-divider  { height: 1px; background: var(--_border); margin-bottom: 14px; }

/* REC indicator */
.eyas-rec { display: none; color: var(--_danger); font-family: var(--font-mono); font-size: .72rem; font-weight: 700; animation: blink 1.4s step-start infinite; }
body.has-feed .eyas-rec { display: inline; }
@keyframes blink { 50% { opacity: 0; } }

/* Tabs */
.tab-nav { border-bottom: 1px solid var(--_border) !important; }
.tab-nav button {
    background: transparent !important; color: var(--_muted) !important;
    border-bottom: 2px solid transparent !important; text-transform: uppercase !important;
    font-size: .72rem !important; letter-spacing: .07em !important; padding: 8px 14px !important;
}
.tab-nav button.selected { color: var(--_accent) !important; border-bottom-color: var(--_accent) !important; }

/* Pipeline steps */
.pipeline-steps { display: flex; flex-direction: column; gap: 6px; padding: 2px 0; }
.pipeline-step {
    display: flex; align-items: center; gap: 10px;
    padding: 8px 14px; border-radius: 6px;
    border: 1px solid var(--_border); background: var(--_panel);
    font-size: 0.82rem; transition: border-color .2s, opacity .2s;
}
.pipeline-step.pending  { opacity: .45; }
.pipeline-step.running  { border-color: var(--_accent); }
.pipeline-step.done     { border-color: var(--_border); }
.pipeline-step.error    { border-color: var(--_danger); }
.ps-icon   { font-size: 1rem; width: 20px; text-align: center; flex-shrink: 0; }
.pipeline-step.running  .ps-icon { color: var(--_accent); animation: blink .9s step-start infinite; }
.pipeline-step.done     .ps-icon { color: var(--_accent); }
.pipeline-step.error    .ps-icon { color: var(--_danger); }
.ps-name   { flex: 1; color: var(--_text); font-weight: 500; }
.ps-detail { color: var(--_muted); font-size: 0.75rem; }

/* DataFrame */
table { background-color: var(--_panel) !important; }
thead, thead tr { background-color: var(--_surface) !important; }
th { color: var(--_accent) !important; font-size: .68rem !important; text-transform: uppercase !important; letter-spacing: .1em !important; border-color: var(--_border) !important; }
td { color: var(--_text) !important; border-color: var(--_border) !important; }
tr:hover td { background-color: var(--_surface) !important; }

/* Zone count numbers */
#count-entrance input, #count-counter input,
#count-back-door input, #count-aisles input {
    font-size: 2rem !important; font-weight: 700 !important;
    text-align: center !important; color: var(--_accent) !important;
}

/* Status output */
#status-box textarea { color: var(--_accent) !important; }

/* Section headings */
.block h3 {
    color: var(--_text) !important; font-size: .8rem !important;
    text-transform: uppercase !important; letter-spacing: .08em !important;
    border-bottom: 1px solid var(--_border); padding-bottom: 6px; margin-bottom: 10px;
}
.block em { color: var(--_muted) !important; }

/* Chatbot bubbles */
.message.user .bubble-wrap { background: var(--_panel)   !important; border-radius: 8px 8px 2px 8px !important; }
.message.bot  .bubble-wrap { background: var(--_surface) !important; border-radius: 8px 8px 8px 2px !important; }

/* Code blocks — always use theme surface/text, never the browser default black */
code, pre,
.prose code, .prose pre,
.message code, .message pre {
    background-color: var(--_surface) !important;
    color: var(--_text) !important;
    border: 1px solid var(--_border) !important;
    border-radius: 4px;
}
code { padding: 1px 5px; }
pre  { padding: 10px 14px !important; }
pre code { background-color: transparent !important; border: none !important; padding: 0 !important; }

/* Scrollbars */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--_panel); }
::-webkit-scrollbar-thumb { background: var(--_border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--_muted); }
"""


def _build_css(p: dict) -> str:
    root = (
        ":root {\n"
        f"    --_accent:  {p['accent']};\n"
        f"    --_panel:   {p['panel']};\n"
        f"    --_surface: {p['surface']};\n"
        f"    --_border:  {p['border']};\n"
        f"    --_text:    {p['text']};\n"
        f"    --_muted:   {p['muted']};\n"
        f"    --_danger:  {p['danger']};\n"
        "}\n"
    )
    return root + _STRUCTURAL_CSS


# ---------------------------------------------------------------------------
# Per-theme font stacks
# ---------------------------------------------------------------------------

_FONTS: Dict[str, list] = {
    # Simple themes — clean sans-serif
    "night":    [fonts.GoogleFont("Inter"), fonts.Font("system-ui"), fonts.Font("sans-serif")],
    "amber":    [fonts.GoogleFont("Inter"), fonts.Font("system-ui"), fonts.Font("sans-serif")],
    "cyber":    [fonts.GoogleFont("Inter"), fonts.Font("system-ui"), fonts.Font("sans-serif")],
    "sentinel": [fonts.GoogleFont("Inter"), fonts.Font("system-ui"), fonts.Font("sans-serif")],
    # Advanced themes
    "voltagent": [fonts.GoogleFont("Inter"), fonts.Font("system-ui"), fonts.Font("sans-serif")],
    "xai":       [fonts.GoogleFont("Inter"), fonts.Font("system-ui"), fonts.Font("sans-serif")],
    "warp":      [fonts.GoogleFont("Inter"), fonts.Font("system-ui"), fonts.Font("sans-serif")],
    "linear":    [fonts.GoogleFont("Inter"), fonts.Font("system-ui"), fonts.Font("sans-serif")],
    "sentry":    [fonts.GoogleFont("Rubik"), fonts.Font("system-ui"), fonts.Font("sans-serif")],
    "stripe":    [fonts.GoogleFont("Inter"), fonts.Font("system-ui"), fonts.Font("sans-serif")],
    "supabase":  [fonts.GoogleFont("Inter"), fonts.Font("system-ui"), fonts.Font("sans-serif")],
    "vercel":    [fonts.GoogleFont("Geist"), fonts.GoogleFont("Inter"), fonts.Font("system-ui"), fonts.Font("sans-serif")],
    "cursor":    [fonts.Font("system-ui"), fonts.Font("Helvetica Neue"), fonts.Font("Arial"), fonts.Font("sans-serif")],
    "runway":    [fonts.GoogleFont("Instrument Serif"), fonts.Font("Georgia"), fonts.Font("serif")],
}

_FONTS_MONO_BY_THEME: Dict[str, list] = {
    "vercel": [fonts.GoogleFont("Geist Mono"), fonts.Font("ui-monospace"), fonts.Font("monospace")],
    "cursor": [fonts.GoogleFont("JetBrains Mono"), fonts.Font("Fira Code"), fonts.Font("ui-monospace"), fonts.Font("monospace")],
}
_FONTS_MONO_DEFAULT = [fonts.GoogleFont("JetBrains Mono"), fonts.Font("ui-monospace"), fonts.Font("Consolas"), fonts.Font("monospace")]


# ---------------------------------------------------------------------------
# Gradio theme — palette baked in at construction time
# ---------------------------------------------------------------------------

class EyasTheme(Base):
    """Surveillance-console Gradio theme. Palette is chosen at startup; restart to change."""

    def __init__(self, color: str = "night", dark: bool = True, advanced: Optional[str] = None) -> None:
        if advanced and advanced in _ADVANCED:
            p = _ADVANCED[advanced]
        else:
            palettes = _DARK if dark else _LIGHT
            p = palettes.get(color, _DARK["night"])

        _fkey = advanced if advanced else color
        super().__init__(
            primary_hue=p["hue"],
            secondary_hue=colors.gray,
            neutral_hue=colors.gray,
            spacing_size=sizes.spacing_md,
            radius_size=sizes.radius_sm,
            text_size=sizes.text_sm,
            font=_FONTS.get(_fkey, _FONTS["night"]),
            font_mono=_FONTS_MONO_BY_THEME.get(_fkey, _FONTS_MONO_DEFAULT),
        )
        super().set(
            # Page
            body_background_fill=p["bg"],         body_background_fill_dark=p["bg"],
            body_text_color=p["text"],             body_text_color_dark=p["text"],
            background_fill_primary=p["panel"],    background_fill_primary_dark=p["panel"],
            background_fill_secondary=p["surface"],background_fill_secondary_dark=p["surface"],
            # Blocks
            block_background_fill=p["panel"],      block_background_fill_dark=p["panel"],
            block_border_color=p["border"],        block_border_color_dark=p["border"],
            block_border_width="1px",
            block_label_text_color=p["label"],     block_label_text_color_dark=p["label"],
            block_label_background_fill=p["panel"],block_label_background_fill_dark=p["panel"],
            # Inputs
            input_background_fill=p["surface"],    input_background_fill_dark=p["surface"],
            input_border_color=p["border"],        input_border_color_dark=p["border"],
            input_border_color_focus=p["accent"],  input_border_color_focus_dark=p["accent"],
            input_placeholder_color=p["muted"],    input_placeholder_color_dark=p["muted"],
            # Primary button
            button_primary_background_fill=p["accent"],      button_primary_background_fill_dark=p["accent"],
            button_primary_background_fill_hover=p["accent_hover"], button_primary_background_fill_hover_dark=p["accent_hover"],
            button_primary_text_color="#ffffff",             button_primary_text_color_dark="#ffffff",
            button_primary_border_color=p["accent"],         button_primary_border_color_dark=p["accent"],
            # Secondary button
            button_secondary_background_fill=p["surface"],   button_secondary_background_fill_dark=p["surface"],
            button_secondary_border_color=p["border"],       button_secondary_border_color_dark=p["border"],
            button_secondary_text_color=p["text"],           button_secondary_text_color_dark=p["text"],
            # Accent
            color_accent=p["accent"],
            color_accent_soft=f"rgba({int(p['accent'][1:3],16)},{int(p['accent'][3:5],16)},{int(p['accent'][5:7],16)},.18)",
        )
        self.name = f"eyas-{advanced or color}-{'adv' if advanced else ('dark' if dark else 'light')}"
        self.custom_css = _build_css(p)


# ---------------------------------------------------------------------------
# JS
# ---------------------------------------------------------------------------

_REC_JS = "(v) => { if (v) document.body.classList.add('has-feed'); else document.body.classList.remove('has-feed'); }"

# ---------------------------------------------------------------------------
# Static HTML
# ---------------------------------------------------------------------------

_HEADER_HTML = """
<div class="eyas-title-row">
    <span class="eyas-rec">&#9679;&nbsp;REC</span>
    <span class="eyas-title">Eyas</span>
</div>
<div class="eyas-tagline">AI Security Camera Agent</div>
<p class="eyas-subtitle">
    Offline AI-powered CCTV analysis &mdash; structured event log,
    security summaries &amp; natural-language queries.
</p>
<div class="eyas-divider"></div>
"""

# ---------------------------------------------------------------------------
# Reusable component helpers
# ---------------------------------------------------------------------------

def _section_title(text: str) -> gr.Markdown:
    return gr.Markdown(f"### {text}")

def _zone_number(label: str, elem_id: str) -> gr.Number:
    return gr.Number(label=label, value=0, interactive=False, elem_id=elem_id)

def _clip_video(label: str) -> gr.Video:
    return gr.Video(label=label, interactive=False)

# ---------------------------------------------------------------------------
# Sample clips — videos shipped in eyas/input/
# ---------------------------------------------------------------------------

_SAMPLES_DIR = Path(__file__).parent.parent / "input"
_SAMPLE_PATHS: Dict[str, str] = {
    p.stem: str(p) for p in sorted(_SAMPLES_DIR.glob("*.mp4"))
}


_STEP_ICONS = {"pending": "○", "running": "●", "done": "✓", "error": "✗"}

_PIPELINE_STEPS_DEFAULT = [
    ("Load video",                  "pending", ""),
    ("Object detection (YOLO)",     "pending", ""),
    ("Semantic analysis (VLM)",     "pending", ""),
    ("LLM summarization",           "pending", ""),
]


def _steps_html(steps: list) -> str:
    rows = []
    for name, state, detail in steps:
        icon = _STEP_ICONS.get(state, "○")
        detail_span = f'<span class="ps-detail">{detail}</span>' if detail else ""
        rows.append(
            f'<div class="pipeline-step {state}">'
            f'<span class="ps-icon">{icon}</span>'
            f'<span class="ps-name">{name}</span>'
            f'{detail_span}'
            f'</div>'
        )
    return '<div class="pipeline-steps">' + "".join(rows) + "</div>"


def _fmt_time(seconds) -> str:
    if seconds is None:
        return ""
    t = float(seconds)
    m, s = divmod(int(t), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _annotate_elapsed(steps: list, start_times: dict) -> list:
    """Append a live elapsed timer to the detail of every running step."""
    import time
    now = time.time()
    result = []
    for i, (name, state, detail) in enumerate(steps):
        if state == "running" and i in start_times:
            secs = int(now - start_times[i])
            m, s = divmod(secs, 60)
            elapsed = f"{m}:{s:02d}"
            detail = f"{detail} · {elapsed}" if detail else elapsed
        result.append((name, state, detail))
    return result


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

def build_app(
    color: str = "night",
    dark: bool = True,
    advanced: Optional[str] = None,
    prefs_path: Optional[Path] = None,
) -> gr.Blocks:

    current_label = (
        _ADVANCED_NAMES.get(advanced, advanced)
        if advanced else _theme_label(color, dark)
    )
    _theme = EyasTheme(color=color, dark=dark, advanced=advanced)

    with gr.Blocks(title="AI Security Camera Agent") as demo:

        # ── Header ──────────────────────────────────────────────────────────
        with gr.Row():
            with gr.Column(scale=5, elem_id="eyas-header"):
                gr.HTML(_HEADER_HTML)
            with gr.Column(scale=1, min_width=160, elem_id="theme-col"):
                gr.HTML(f'<div class="eyas-theme-badge">Theme: <strong>{current_label}</strong></div>')

        event_log_state: gr.State = gr.State([])

        # ── Input row ───────────────────────────────────────────────────────
        with gr.Row():
            with gr.Column(scale=3):
                with gr.Row():
                    sample_dd = gr.Dropdown(
                        choices=list(_SAMPLE_PATHS.keys()),
                        label="Sample clips",
                        interactive=True,
                        scale=4,
                    )
                    load_sample_btn = gr.Button("Load", variant="secondary", scale=1, size="sm")
                video_input = gr.Video(label="Upload CCTV clip (.mp4)", sources=["upload"])
            with gr.Column(scale=1):
                analyze_btn  = gr.Button("Analyze", variant="primary", size="lg")
                status_box   = gr.Textbox(label="Status", interactive=False, lines=3, elem_id="status-box")
                upload_status = gr.Textbox(label="Storage", interactive=False, lines=1, visible=True)

        video_input.change(fn=None, inputs=[video_input], js=_REC_JS)

        # ── Pipeline progress ────────────────────────────────────────────────
        pipeline_html = gr.HTML(_steps_html(_PIPELINE_STEPS_DEFAULT))

        # ── Tabs ────────────────────────────────────────────────────────────
        with gr.Tabs():

            with gr.TabItem("Event Timeline"):
                _section_title("Detected Events")
                event_table = gr.DataFrame(
                    headers=["#", "Type", "Start", "End", "Zone", "Confidence", "Clip"],
                    label="Event Log", interactive=False, wrap=True,
                )
                with gr.Row():
                    with gr.Column(scale=2):
                        clip_selector = gr.Dropdown(label="Select clip to preview", choices=[], interactive=True)
                    with gr.Column(scale=3):
                        _clip_video("Clip Preview")

            with gr.TabItem("Summary & Alerts"):
                with gr.Row():
                    with gr.Column():
                        _section_title("AI Security Summary")
                        summary_box = gr.Textbox(label="Overnight Summary", lines=6, interactive=False)
                        risk_badge  = gr.Label(label="Risk Level")
                    with gr.Column():
                        _section_title("Flagged Items")
                        flags_box = gr.JSON(label="Flags")
                        suspicious_clips_dd = gr.Dropdown(
                            label="Suspicious clips — select to preview", choices=[], interactive=True,
                        )
                        _clip_video("Flagged Clip Preview")

            with gr.TabItem("Ask Footage"):
                _section_title("Ask a question about the footage")
                gr.Markdown(
                    "*e.g. 'Anything unusual overnight?', "
                    "'Show back door activity', "
                    "'What happened between 2–4 AM?'*"
                )
                chatbot = gr.Chatbot(label="Footage Q&A", height=420)
                with gr.Row():
                    query_input = gr.Textbox(
                        placeholder="Ask about the footage...", label="Your question", scale=5, lines=1,
                    )
                    ask_btn = gr.Button("Ask", variant="primary", scale=1)
                clear_btn = gr.Button("Clear chat", variant="secondary", size="sm")

            with gr.TabItem("Detection Metrics"):
                _section_title("Per-Zone Object Counts")
                with gr.Row():
                    count_entrance  = _zone_number("Entrance",  "count-entrance")
                    count_counter   = _zone_number("Counter",   "count-counter")
                    count_back_door = _zone_number("Back Door", "count-back-door")
                    count_aisles    = _zone_number("Aisles",    "count-aisles")
                metrics_json = gr.JSON(label="Raw detection counts by zone")

            with gr.TabItem("Audio Report"):
                _section_title("Spoken Security Report")
                gr.Markdown(
                    "Generates a spoken playback of the AI security summary using VoxCPM2 TTS. "
                    "Run **Analyze** first, then click the button below."
                )
                audio_output      = gr.Audio(label="TTS Report", interactive=False)
                generate_audio_btn = gr.Button("Generate Audio Report", variant="secondary")

            # ── Live Feed ────────────────────────────────────────────────────
            with gr.TabItem("Live Feed"):
                _section_title("Camera Stream")
                gr.Markdown(
                    "*Enter an RTSP URL, a file path, or `0` for the default webcam. "
                    "Click **Start** to connect.*"
                )
                with gr.Row():
                    stream_src = gr.Textbox(
                        placeholder="rtsp://192.168.1.x:554/stream  or  0",
                        label="Source", scale=4, lines=1,
                    )
                    start_stream_btn = gr.Button("Start", variant="primary", scale=1)
                    stop_stream_btn  = gr.Button("Stop",  variant="secondary", scale=1)

                stream_status = gr.Textbox(label="Stream status", interactive=False, lines=1)
                live_image    = gr.Image(label="Live Feed", interactive=False, height=420)
                feed_timer    = gr.Timer(value=0.1, active=False)

                with gr.Row():
                    start_rec_btn = gr.Button("Start Recording", variant="primary")
                    stop_rec_btn  = gr.Button("Stop Recording",  variant="secondary")
                rec_status = gr.Textbox(label="Recording", interactive=False, lines=1)

            # ── Clip Library ─────────────────────────────────────────────────
            with gr.TabItem("Clip Library"):
                _section_title("Stored Clips")
                with gr.Row():
                    refresh_lib_btn = gr.Button("Refresh", size="sm", variant="secondary")
                    lib_dd = gr.Dropdown(
                        label="Clips", choices=storage.choices(), interactive=True, scale=4,
                    )
                    load_clip_btn   = gr.Button("Load for Analysis", variant="primary", scale=1)
                    delete_clip_btn = gr.Button("Delete", variant="stop", scale=1)

                lib_status   = gr.Textbox(label="Status", interactive=False, lines=1)
                lib_preview  = gr.Video(label="Preview", interactive=False)

            with gr.TabItem("Settings"):
                _section_title("Simple Theme")
                gr.Markdown(
                    "Pick a color and mode, then click **Save**. "
                    "Restart the server to apply."
                )
                with gr.Row():
                    color_dd = gr.Dropdown(
                        choices=list(_COLOR_NAMES.values()),
                        value=_COLOR_NAMES[color],
                        label="Color",
                        interactive=True,
                    )
                    mode_dd = gr.Dropdown(
                        choices=["Dark", "Light"],
                        value="Dark" if dark else "Light",
                        label="Mode",
                        interactive=True,
                    )
                save_btn     = gr.Button("Save theme", variant="secondary", size="sm")
                theme_status = gr.Markdown("")

                gr.HTML("<hr style='border-color:var(--_border);margin:18px 0;'>")
                _section_title("Advanced Theme")
                gr.Markdown(
                    "DESIGN.md-sourced palettes from real production websites. "
                    "See `designs/` for the source files."
                )
                advanced_dd = gr.Dropdown(
                    choices=list(_ADVANCED_NAMES.values()),
                    value=_ADVANCED_NAMES.get(advanced) if advanced else None,
                    label="Advanced Theme",
                    interactive=True,
                )
                save_adv_btn    = gr.Button("Save advanced theme", variant="secondary", size="sm")
                adv_theme_status = gr.Markdown("")

        # ── Callbacks ───────────────────────────────────────────────────────

        _CLIPS_DIR = str(Path(__file__).parent.parent / "data" / "clips")

        _INPUTS_DIR = str(Path(__file__).parent.parent / "input")

        # Upload → auto-store (skip clips-dir and built-in sample files)
        def on_upload(video_path):
            if video_path is None:
                return ""
            norm = video_path.replace("\\", "/")
            if _CLIPS_DIR.replace("\\", "/") in norm:
                return "Clip from library — already stored."
            if _INPUTS_DIR.replace("\\", "/") in norm:
                return "Sample clip — not stored."
            try:
                entry = storage.store(video_path, source="upload")
                return f"Stored: {entry['filename']}  ({entry['size_mb']} MB)"
            except Exception as exc:
                return f"Storage error: {exc}"

        video_input.change(on_upload, inputs=[video_input], outputs=[upload_status])

        def load_sample(name: str):
            return _SAMPLE_PATHS.get(name)

        load_sample_btn.click(load_sample, inputs=[sample_dd], outputs=[video_input])

        def run_pipeline(video_path):
            import tempfile
            import time as _time
            from visual_pipeline import run_visual_pipeline
            from llm.reasoner import summarize_events as _summarize

            steps = list(_PIPELINE_STEPS_DEFAULT)  # mutable copy
            step_start: dict = {}

            def _blank():
                return ([], [], gr.update(choices=[]), "", {"none": 1.0},
                        [], gr.update(choices=[]), {}, 0, 0, 0, 0)

            def emit(status):
                return (_steps_html(_annotate_elapsed(steps, step_start)), status) + _blank()

            def _start_step(idx: int, name: str, detail: str = "") -> None:
                step_start[idx] = _time.time()
                steps[idx] = (name, "running", detail)

            def _finish_step(idx: int, name: str, detail: str = "") -> None:
                step_start.pop(idx, None)
                steps[idx] = (name, "done", detail)

            if video_path is None:
                steps[0] = ("Load video", "error", "No video selected")
                yield emit("No video uploaded.")
                return

            # ── Step 1: load ────────────────────────────────────────────────
            _start_step(0, "Load video")
            yield emit("Loading video…")

            _finish_step(0, "Load video", Path(video_path).name)
            _start_step(1, "Object detection (YOLO)", "starting…")
            steps[2] = ("Semantic analysis (VLM)", "pending", "")
            yield emit("Running YOLO + event structuring…")

            # ── Step 2: visual pipeline (threaded so progress yields work) ───
            import queue as _queue
            import threading as _threading

            output_dir = tempfile.mkdtemp(prefix="eyas_out_")
            _q: _queue.Queue = _queue.Queue()

            def _on_progress(done: int, total: int, track_count: int, vlm_fired: bool) -> None:
                _q.put(("progress", done, total, track_count, vlm_fired))

            def _run() -> None:
                try:
                    result = run_visual_pipeline(
                        video_path=video_path,
                        output_dir=output_dir,
                        write_annotated_video=False,
                        progress=_on_progress,
                    )
                    _q.put(("done", result))
                except Exception as exc:
                    _q.put(("error", exc))

            _threading.Thread(target=_run, daemon=True).start()

            vp = None
            _model_loaded = False
            while True:
                try:
                    msg = _q.get(timeout=1.0)
                except _queue.Empty:
                    # Still in model-load phase — pulse the detail so the user knows
                    if not _model_loaded:
                        steps[1] = ("Object detection (YOLO)", "running", "loading model weights…")
                        steps[2] = ("Semantic analysis (VLM)", "running", "loading model weights…")
                        yield emit("Loading YOLO + VLM weights…")
                    else:
                        # Already processing — re-yield to refresh elapsed timers
                        yield emit(f"Processing…")
                    continue

                kind = msg[0]
                if kind == "progress":
                    if not _model_loaded:
                        _model_loaded = True
                        step_start[1] = _time.time()
                    _, done, total, track_count, vlm_fired = msg
                    pct = f"{done}/{total}" if total else str(done)
                    person_s = f"{track_count} person{'s' if track_count != 1 else ''}"
                    steps[1] = ("Object detection (YOLO)", "running", f"frame {pct} · {person_s}")
                    if vlm_fired:
                        if 2 not in step_start:
                            step_start[2] = _time.time()
                        steps[2] = ("Semantic analysis (VLM)", "running", f"frame {pct}")
                    yield emit(f"Processing frame {pct}…")
                elif kind == "done":
                    vp = msg[1]
                    break
                else:
                    steps[1] = ("Object detection (YOLO)", "error", str(msg[1])[:80])
                    steps[2] = ("Semantic analysis (VLM)", "error", "")
                    yield emit(f"Pipeline error: {msg[1]}")
                    return

            events: List[Dict] = vp.events
            _finish_step(1, "Object detection (YOLO)",
                         f"{vp.frames_processed} frames · {vp.unique_tracks} tracks")
            _finish_step(2, "Semantic analysis (VLM)", f"{len(events)} events")
            _start_step(3, "LLM summarization")

            rows = []
            for i, ev in enumerate(events):
                activity = "pickup" if ev.get("pickup_confirmed") else ev.get("activity", "")
                rows.append([
                    i, activity,
                    _fmt_time(ev.get("timestamp")),
                    _fmt_time(ev.get("confirmation_timestamp")),
                    ev.get("zone", ""),
                    round(float(ev.get("confidence", 0)), 2),
                    "",
                ])
            zone_counts = {"entrance": 0, "counter": 0, "back_door": 0, "aisles": 0}
            for ev in events:
                z = ev.get("zone", "").lower().replace(" ", "_")
                if z in zone_counts:
                    zone_counts[z] += 1

            yield (
                _steps_html(_annotate_elapsed(steps, step_start)), "Running LLM summarization…",
                events, rows, gr.update(choices=[]),
                "", {"none": 1.0}, [], gr.update(choices=[]),
                zone_counts,
                zone_counts["entrance"], zone_counts["counter"],
                zone_counts["back_door"], zone_counts["aisles"],
            )

            # ── Step 3: LLM ─────────────────────────────────────────────────
            try:
                llm = _summarize(events)
            except Exception:
                llm = {"summary": "LLM unavailable — no model loaded.",
                       "flags": [], "suspicious_clips": [], "risk_level": "none"}

            _finish_step(3, "LLM summarization", f"risk: {llm['risk_level']}")
            status = (
                f"Done. {vp.frames_processed} frames · "
                f"{vp.unique_tracks} tracks · {len(events)} events."
            )
            yield (
                _steps_html(_annotate_elapsed(steps, step_start)), status,
                events, rows, gr.update(choices=[]),
                llm["summary"], {llm["risk_level"]: 1.0},
                llm["flags"], gr.update(choices=llm["suspicious_clips"]),
                zone_counts,
                zone_counts["entrance"], zone_counts["counter"],
                zone_counts["back_door"], zone_counts["aisles"],
            )

        analyze_btn.click(
            run_pipeline,
            inputs=[video_input],
            outputs=[
                pipeline_html, status_box,
                event_log_state, event_table, clip_selector,
                summary_box, risk_badge, flags_box, suspicious_clips_dd,
                metrics_json, count_entrance, count_counter, count_back_door, count_aisles,
            ],
        )

        def ask_footage(message: str, history: list, events: List[Dict]):
            if not message.strip():
                return history, ""
            if not events:
                reply = "No events loaded yet — please upload and analyze a video first."
            else:
                from llm.reasoner import answer_query as _answer
                try:
                    result = _answer(events, message)
                    reply  = result["answer"]
                    if result.get("clips"):
                        reply += "\n\nRelated clips: " + ", ".join(result["clips"])
                except Exception as exc:
                    reply = f"LLM error: {exc}"
            return history + [(message, reply)], ""

        ask_btn.click(ask_footage, inputs=[query_input, chatbot, event_log_state], outputs=[chatbot, query_input])
        query_input.submit(ask_footage, inputs=[query_input, chatbot, event_log_state], outputs=[chatbot, query_input])
        clear_btn.click(lambda: ([], ""), outputs=[chatbot, query_input])

        def generate_audio(events: List[Dict]):
            if not events:
                return None
            try:
                from llm.reasoner import summarize_events as _summarize
                llm = _summarize(events)
                text = llm.get("summary", "").strip()
                if not text:
                    return None
                from postprocessing.translate_tts import tts
                import numpy as np
                chunks = list(tts(text, target_lang="English"))
                if not chunks:
                    return None
                sample_rate = chunks[0][0]
                audio = np.concatenate([c[1] for c in chunks])
                return sample_rate, audio
            except Exception:
                return None

        generate_audio_btn.click(generate_audio, inputs=[event_log_state], outputs=[audio_output])

        # ── Live Feed callbacks ──────────────────────────────────────────────

        def start_stream(src: str):
            src = src.strip()
            if not src:
                return "No source specified.", gr.Timer(active=False)
            try:
                source = int(src) if src.isdigit() else src
                _stream.start(source)
                return f"Connected: {src}", gr.Timer(active=True)
            except Exception as exc:
                return f"Error: {exc}", gr.Timer(active=False)

        def stop_stream():
            _stream.stop()
            return "Stream stopped.", gr.Timer(active=False)

        def poll_frame():
            return _stream.get_rgb()

        def start_recording():
            if not _stream.is_open():
                return "No active stream."
            path = _stream.start_recording()
            return f"Recording → {path}"

        def stop_recording():
            path = _stream.stop_recording()
            if path is None:
                return "No recording in progress."
            try:
                entry = storage.store(path, source="stream")
                return f"Saved: {entry['filename']}  ({entry['size_mb']} MB)"
            except Exception as exc:
                return f"Saved to {path}. Storage error: {exc}"

        start_stream_btn.click(start_stream, inputs=[stream_src],  outputs=[stream_status, feed_timer])
        stop_stream_btn.click(stop_stream,   inputs=[],            outputs=[stream_status, feed_timer])
        feed_timer.tick(poll_frame, outputs=[live_image])
        start_rec_btn.click(start_recording, outputs=[rec_status])
        stop_rec_btn.click(stop_recording,   outputs=[rec_status])

        # ── Clip Library callbacks ───────────────────────────────────────────

        def refresh_library():
            return gr.update(choices=storage.choices())

        def preview_clip(choice: str):
            path = storage.path_from_choice(choice) if choice else None
            return path

        def load_for_analysis(choice: str):
            path = storage.path_from_choice(choice) if choice else None
            if path is None:
                return None, "Clip not found."
            return path, f"Loaded: {choice}"

        def delete_clip(choice: str):
            if not choice:
                return "Nothing selected.", gr.update(choices=storage.choices())
            filename = choice.split(" — ", 1)[1].split("  ")[0].strip() if " — " in choice else ""
            ok = storage.delete(filename) if filename else False
            msg = f"Deleted {filename}." if ok else "Delete failed."
            return msg, gr.update(choices=storage.choices())

        refresh_lib_btn.click(refresh_library, outputs=[lib_dd])
        lib_dd.change(preview_clip, inputs=[lib_dd], outputs=[lib_preview])
        load_clip_btn.click(load_for_analysis, inputs=[lib_dd], outputs=[video_input, lib_status])
        delete_clip_btn.click(delete_clip, inputs=[lib_dd], outputs=[lib_status, lib_dd])

        def save_theme(color_label: str, mode_label: str) -> str:
            if prefs_path is None:
                return "No preferences file path set."
            c = _COLOR_KEY.get(color_label, "night")
            d = mode_label == "Dark"
            try:
                prefs_path.write_text(json.dumps({"theme": c, "dark": d}, indent=2))
                return f"Saved **{color_label} · {mode_label}**. Restart the server to apply."
            except Exception as exc:
                return f"Error saving preferences: {exc}"

        save_btn.click(save_theme, inputs=[color_dd, mode_dd], outputs=[theme_status])

        def save_advanced_theme(adv_label: str) -> str:
            if prefs_path is None:
                return "No preferences file path set."
            key = _ADVANCED_KEY.get(adv_label)
            if key is None:
                return f"Unknown advanced theme: {adv_label}"
            try:
                prefs_path.write_text(json.dumps({"advanced": key}, indent=2))
                return f"Saved **{adv_label}**. Restart the server to apply."
            except Exception as exc:
                return f"Error saving preferences: {exc}"

        save_adv_btn.click(save_advanced_theme, inputs=[advanced_dd], outputs=[adv_theme_status])

    return demo, _theme
