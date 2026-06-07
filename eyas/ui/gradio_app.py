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

_THEME_CHOICES = [
    "Night Vision · Dark",   "Night Vision · Light",
    "Amber CRT · Dark",      "Amber CRT · Light",
    "Cyberpunk · Dark",      "Cyberpunk · Light",
    "Sentinel · Dark",       "Sentinel · Light",
]

_LABEL_TO_KEY: Dict[str, tuple] = {
    "Night Vision · Dark":   ("night",    True),
    "Night Vision · Light":  ("night",    False),
    "Amber CRT · Dark":      ("amber",    True),
    "Amber CRT · Light":     ("amber",    False),
    "Cyberpunk · Dark":      ("cyber",    True),
    "Cyberpunk · Light":     ("cyber",    False),
    "Sentinel · Dark":       ("sentinel", True),
    "Sentinel · Light":      ("sentinel", False),
}


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
#eyas-header, #eyas-header .block, #eyas-header .form,
#theme-col,   #theme-col .block,   #theme-col .form {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
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
# Gradio theme — palette baked in at construction time
# ---------------------------------------------------------------------------

class EyasTheme(Base):
    """Surveillance-console Gradio theme. Palette is chosen at startup; restart to change."""

    def __init__(self, color: str = "night", dark: bool = True) -> None:
        palettes = _DARK if dark else _LIGHT
        p = palettes.get(color, _DARK["night"])

        super().__init__(
            primary_hue=p["hue"],
            secondary_hue=colors.gray,
            neutral_hue=colors.gray,
            spacing_size=sizes.spacing_md,
            radius_size=sizes.radius_sm,
            text_size=sizes.text_sm,
            font=[fonts.Font("Courier New"), fonts.Font("Consolas"), fonts.Font("ui-monospace")],
            font_mono=[fonts.Font("Courier New"), fonts.Font("Consolas"), fonts.Font("ui-monospace")],
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
        self.name = f"eyas-{color}-{'dark' if dark else 'light'}"
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
# App
# ---------------------------------------------------------------------------

def build_app(
    color: str = "night",
    dark: bool = True,
    prefs_path: Optional[Path] = None,
) -> gr.Blocks:

    current_label = _theme_label(color, dark)

    with gr.Blocks(title="AI Security Camera Agent") as demo:

        # ── Header ──────────────────────────────────────────────────────────
        with gr.Row():
            with gr.Column(scale=5, elem_id="eyas-header"):
                gr.HTML(_HEADER_HTML)
            with gr.Column(scale=1, min_width=200, elem_id="theme-col"):
                gr.Markdown(f"**{current_label}**")

        event_log_state: gr.State = gr.State([])

        # ── Input row ───────────────────────────────────────────────────────
        with gr.Row():
            with gr.Column(scale=3):
                video_input = gr.Video(label="Upload CCTV clip (.mp4)", sources=["upload"])
            with gr.Column(scale=1):
                analyze_btn = gr.Button("Analyze", variant="primary", size="lg")
                status_box  = gr.Textbox(label="Status", interactive=False, lines=3, elem_id="status-box")

        video_input.change(fn=None, inputs=[video_input], js=_REC_JS)

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
                    "Generates a TTS audio playback of the AI summary "
                    "*(requires translation/TTS stage to be wired in)*."
                )
                audio_output      = gr.Audio(label="TTS Report", interactive=False)
                generate_audio_btn = gr.Button("Generate Audio Report", variant="secondary")

            with gr.TabItem("Settings"):
                _section_title("Theme")
                gr.Markdown(
                    "Select a theme and click **Save**. "
                    "Then restart the server to apply it."
                )
                theme_dd = gr.Dropdown(
                    choices=_THEME_CHOICES,
                    value=current_label,
                    label="Theme",
                    interactive=True,
                )
                save_btn      = gr.Button("Save theme", variant="secondary", size="sm")
                theme_status  = gr.Markdown("")

        # ── Callbacks ───────────────────────────────────────────────────────

        def run_pipeline(video_path):
            if video_path is None:
                return (
                    "No video uploaded.", [], [], gr.Dropdown(choices=[]),
                    "", {}, [], gr.Dropdown(choices=[]), {}, 0, 0, 0, 0,
                )
            # TODO: wire real pipeline stages
            events: List[Dict] = []
            result = {
                "summary": "(prototype) pipeline not yet connected.",
                "flags": [], "suspicious_clips": [], "risk_level": "none",
            }
            rows = [
                [i, ev.get("type"), ev.get("start_time"), ev.get("end_time"),
                 ev.get("zone"), round(ev.get("metadata", {}).get("confidence", 0), 2),
                 ev.get("metadata", {}).get("clip_pointer", "")]
                for i, ev in enumerate(events)
            ]
            clips      = list({ev.get("metadata", {}).get("clip_pointer", "") for ev in events} - {""})
            zone_counts = {"entrance": 0, "counter": 0, "back_door": 0, "aisles": 0}
            return (
                f"Done. {len(events)} event(s) detected.",
                events, rows, gr.Dropdown(choices=clips),
                result["summary"], {result["risk_level"]: 1.0},
                result["flags"], gr.Dropdown(choices=result["suspicious_clips"]),
                zone_counts,
                zone_counts["entrance"], zone_counts["counter"],
                zone_counts["back_door"], zone_counts["aisles"],
            )

        analyze_btn.click(
            run_pipeline,
            inputs=[video_input],
            outputs=[
                status_box, event_log_state, event_table, clip_selector,
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
                # TODO: result = answer_query(events, message)
                result = {"answer": "(prototype) LLM not yet connected.", "relevant_event_indices": [], "clips": []}
                reply  = result["answer"]
                if result["clips"]:
                    reply += "\n\nRelated clips: " + ", ".join(result["clips"])
            return history + [(message, reply)], ""

        ask_btn.click(ask_footage, inputs=[query_input, chatbot, event_log_state], outputs=[chatbot, query_input])
        query_input.submit(ask_footage, inputs=[query_input, chatbot, event_log_state], outputs=[chatbot, query_input])
        clear_btn.click(lambda: ([], ""), outputs=[chatbot, query_input])

        def generate_audio(events: List[Dict]):
            if not events:
                return None
            # TODO: from eyas.postprocessing.translate_tts import translate_and_speak
            return None

        generate_audio_btn.click(generate_audio, inputs=[event_log_state], outputs=[audio_output])

        def save_theme(label: str) -> str:
            if prefs_path is None:
                return "⚠ No preferences file path set."
            c, d = _LABEL_TO_KEY.get(label, ("night", True))
            try:
                prefs_path.write_text(json.dumps({"theme": c, "dark": d}, indent=2))
                return f"Saved **{label}**. Restart the server to apply."
            except Exception as exc:
                return f"Error saving preferences: {exc}"

        save_btn.click(save_theme, inputs=[theme_dd], outputs=[theme_status])

    return demo
