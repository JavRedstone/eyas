"""Gradio UI for Eyas — AI Security Camera Agent."""

import json
import sys
import traceback
from pathlib import Path
from typing import Dict, List, Optional

# Direct execution puts ``ui/`` first on sys.path, causing ``ui/locale.py`` to
# shadow Python's standard-library ``locale`` module when Gradio imports pandas.
_EYAS_ROOT = str(Path(__file__).resolve().parents[1])
_UI_ROOT = str(Path(__file__).resolve().parent)
if sys.path and str(Path(sys.path[0]).resolve()) == _UI_ROOT:
    sys.path.pop(0)
if _EYAS_ROOT not in sys.path:
    sys.path.insert(0, _EYAS_ROOT)

import gradio as gr
from gradio.themes.base import Base
from gradio.themes.utils import colors, fonts, sizes

from storage import manager as storage
import model_registry as _mreg
from ui.locale import (
    LANGUAGE_KEY,
    LANGUAGE_LABELS,
    SPLASH_MODEL_KEYS,
    Strings,
    display_risk,
    fmt_event_time,
    format_event_row,
    format_translation_time,
    localize_llm_result,
    localize_text,
    pipeline_steps_default,
)

_mreg.start()

# ---------------------------------------------------------------------------
# Hawk Vision palette — single fixed theme
# ---------------------------------------------------------------------------

_HAWK = dict(
    bg="#1C1C1C",            # Soot Black
    panel="#3D2314",         # Deep Chocolate Brown
    surface="#5C4033",       # Earth Brown
    border="#7A5545",        # Warm dark brown (harmonises with earth palette)
    accent="#B85A38",        # Cinnamon Red  — primary
    accent_hover="#D06A4C",  # Rusty Red-Orange — primary hover
    text="#F5EAD4",          # Cream / Pale Buff
    muted="#9C8878",         # Warm muted
    danger="#E05A3A",        # Warm red-orange danger
    label="#A09080",         # Light warm muted
)


# ---------------------------------------------------------------------------
# CSS — palette values baked in at startup via _build_css(palette)
# ---------------------------------------------------------------------------

_STRUCTURAL_CSS = """
/* ── Design tokens ───────────────────────────────────────────────────── */
:root {
    /* Radius scale */
    --r-xs:   4px;   /* code snippets, tiny pills           */
    --r-sm:   8px;   /* inputs, pipeline steps, table       */
    --r-card: 12px;  /* cards, panels, dialogs              */
    --r-btn:  20px;  /* all buttons (MD3 filled/tonal pill) */
    --r-nav:  28px;  /* navigation rail indicators          */

    /* Shadow scale (warm-toned dark) */
    --sh-sm: 0 1px 3px rgba(0,0,0,.40);
    --sh-md: 0 2px 8px rgba(0,0,0,.45);
    --sh-lg: 0 4px 14px rgba(0,0,0,.55);

    /* Button heights */
    --btn-h:    36px;
    --btn-h-lg: 44px;
}

footer { display: none !important; }
.app-title, .main-header h1, h1.title,
.gradio-container > .main > .wrap > .prose h1:first-child { display: none !important; }

/* ── Header wrappers ─────────────────────────────────────────────────── */
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

/* Badge */
.eyas-theme-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: var(--_surface);
    border: 1px solid var(--_border);
    border-radius: var(--r-sm);
    padding: 5px 11px;
    font-size: 0.72rem;
    color: var(--_muted);
    letter-spacing: 0.03em;
    white-space: nowrap;
    line-height: 1.4;
}
.eyas-theme-badge strong { color: var(--_text); font-weight: 600; }

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

/* ── Card panels ─────────────────────────────────────────────────────── */
#eyas-sidebar {
    background: var(--_panel) !important;
    border: 1px solid var(--_border) !important;
    border-radius: var(--r-card) !important;
    box-shadow: var(--sh-md) !important;
    overflow: hidden !important;
    padding: 0 !important;
}
#eyas-sidebar .block, #eyas-sidebar .form,
#eyas-sidebar .block-container, #eyas-sidebar > div > div {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    border-radius: 0 !important;
}

#eyas-main {
    background: var(--_surface) !important;
    border: 1px solid var(--_border) !important;
    border-radius: var(--r-card) !important;
    box-shadow: var(--sh-md) !important;
    overflow: hidden !important;
    padding: 0 !important;
}
#eyas-main .block, #eyas-main .form,
#eyas-main .block-container, #eyas-main > div > div {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    border-radius: 0 !important;
}

/* Inputs inside cards */
#eyas-sidebar input, #eyas-sidebar textarea, #eyas-sidebar select,
#eyas-main    input, #eyas-main    textarea, #eyas-main    select {
    background: var(--_panel) !important;
    border: 1px solid var(--_border) !important;
    border-radius: var(--r-sm) !important;
}
#eyas-sidebar input:focus, #eyas-sidebar textarea:focus,
#eyas-main    input:focus, #eyas-main    textarea:focus {
    border-color: var(--_accent) !important;
    outline: none !important;
}

/* Panel header strip */
.eyas-panel-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: var(--font-mono);
    font-size: 0.6rem;
    font-weight: 700;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--_muted);
    background: var(--_panel);
    border-bottom: 1px solid var(--_border);
    padding: 10px 16px;
}
.eyas-panel-header .ph-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: var(--_accent);
    flex-shrink: 0;
    box-shadow: 0 0 5px var(--_accent);
}
.eyas-panel-header .ph-label { color: var(--_text); }

/* ── Buttons ─────────────────────────────────────────────────────────── */
/* MD3 system: all buttons are pills — filled (primary) or tonal (secondary) */

/* Base pill shape + min height for every button */
button, .btn {
    border-radius: var(--r-btn) !important;
    min-height: var(--btn-h) !important;
}

/* Primary — filled */
button.primary, button[data-testid="primary"],
button.lg.primary {
    border-radius: var(--r-btn) !important;
    min-height: var(--btn-h) !important;
    box-shadow: var(--sh-sm) !important;
    transition: box-shadow 0.12s ease, transform 0.08s ease !important;
}
button.primary:hover, button[data-testid="primary"]:hover {
    box-shadow: var(--sh-md) !important;
    transform: translateY(-1px) !important;
}
button.primary:active, button[data-testid="primary"]:active {
    box-shadow: none !important;
    transform: translateY(1px) !important;
}

/* Secondary — tonal (accent tint fill, accent text, no hard outline) */
button.secondary, button[data-testid="secondary"] {
    border-radius: var(--r-btn) !important;
    min-height: var(--btn-h) !important;
    background: var(--_accent-a12) !important;
    border: 1px solid transparent !important;
    color: var(--_accent) !important;
    box-shadow: none !important;
    transition: background 0.12s ease, border-color 0.12s ease !important;
}
button.secondary:hover, button[data-testid="secondary"]:hover {
    background: var(--_accent-a08) !important;
    border-color: var(--_border) !important;
}

/* Stop / danger button */
button.stop, button[data-testid="stop"] {
    border-radius: var(--r-btn) !important;
    min-height: var(--btn-h) !important;
}

/* Analyze button — large filled pill with icon + physical press */
div:has(> #analyze-btn),
div:has(> #load-sample-btn) {
    padding: 0 16px !important;
    box-sizing: border-box !important;
}
#analyze-btn {
    font-family: var(--font-mono) !important;
    font-size: 0.88rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    border-radius: var(--r-btn) !important;
    min-height: var(--btn-h-lg) !important;
    width: 100% !important;
    margin: 0 !important;
    box-shadow: 0 4px 0 rgba(0,0,0,.45), var(--sh-sm) !important;
    transform: translateY(0) !important;
    transition: transform 0.08s ease, box-shadow 0.08s ease !important;
    text-decoration: none !important;
}
#analyze-btn::before {
    content: "play_arrow";
    font-family: 'Material Symbols Outlined' !important;
    font-style: normal !important;
    font-size: 19px !important;
    line-height: 1 !important;
    margin-right: 8px !important;
    vertical-align: middle !important;
    font-weight: 400 !important;
}
#analyze-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 0 rgba(0,0,0,.45), var(--sh-md) !important;
}
#analyze-btn:active {
    transform: translateY(2px) !important;
    box-shadow: 0 1px 0 rgba(0,0,0,.45) !important;
}

/* Refresh icon button — same pill, compact */
#refresh-events-btn {
    padding: 0 10px !important;
    min-width: 36px !important;
    max-width: 36px !important;
    min-height: var(--btn-h) !important;
    border-radius: var(--r-btn) !important;
}
#refresh-events-btn::before {
    content: "refresh";
    font-family: 'Material Symbols Outlined' !important;
    font-style: normal !important;
    font-size: 18px !important;
    line-height: 1 !important;
    font-weight: 400 !important;
    vertical-align: middle !important;
}

/* ── Sidebar navigation tabs ─────────────────────────────────────────── */
.tabs {
    display: flex !important;
    flex-direction: row !important;
    align-items: stretch !important;
    gap: 0 !important;
    background: var(--_panel) !important;
    border: 1px solid var(--_border) !important;
    border-radius: var(--r-card) !important;
    box-shadow: var(--sh-md) !important;
    overflow: hidden !important;
}
.tab-wrapper {
    display: flex !important;
    flex-direction: column !important;
    width: 200px !important;
    min-width: 200px !important;
    flex-shrink: 0 !important;
    border-right: 1px solid var(--_border) !important;
    background: transparent !important;
    align-self: stretch !important;
    padding: 8px 0 !important;
}
.tab-container.visually-hidden { display: none !important; }
.overflow-menu { display: none !important; }
.tab-container {
    display: flex !important;
    flex-direction: column !important;
    height: auto !important;
    overflow: visible !important;
    gap: 1px !important;
    border: none !important;
    width: 100% !important;
}

/* Nav rail buttons */
.tab-container button {
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    padding: 10px 14px 10px 12px !important;
    margin: 1px 6px !important;
    width: calc(100% - 12px) !important;
    text-align: left !important;
    justify-content: flex-start !important;
    font-size: 0.83rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.01em !important;
    text-transform: none !important;
    text-decoration: none !important;
    color: var(--_muted) !important;
    background: transparent !important;
    border: none !important;
    border-bottom: none !important;
    outline: none !important;
    border-radius: var(--r-nav) !important;
    min-height: unset !important;
    box-shadow: none !important;
    transition: background 0.13s, color 0.13s !important;
    cursor: pointer !important;
}
.tab-container button:hover {
    background: var(--_accent-a08) !important;
    color: var(--_text) !important;
}
.tab-container button.selected,
.tab-container button[aria-selected="true"] {
    color: var(--_accent) !important;
    background: var(--_accent-a12) !important;
    font-weight: 600 !important;
    text-decoration: none !important;
    border: none !important;
    border-bottom: none !important;
    box-shadow: none !important;
    outline: none !important;
}
.tab-container button::after,
.tab-container button.selected::after,
.tab-container button[aria-selected="true"]::after { display: none !important; content: none !important; }
.tab-container button:focus, .tab-container button:focus-visible { outline: none !important; box-shadow: none !important; }

/* Material Symbol icons */
.tab-container button::before {
    font-family: 'Material Symbols Outlined' !important;
    font-style: normal !important;
    font-size: 18px !important;
    line-height: 1 !important;
    display: inline-block !important;
    flex-shrink: 0 !important;
    color: inherit !important;
    opacity: 0.75;
}
.tab-container button:nth-child(1)::before { content: "timeline"; }
.tab-container button:nth-child(2)::before { content: "notifications_active"; }
.tab-container button:nth-child(3)::before { content: "forum"; }
.tab-container button:nth-child(4)::before { content: "monitoring"; }
.tab-container button:nth-child(5)::before { content: "volume_up"; }
.tab-container button:nth-child(6)::before { content: "video_library"; }
.tab-container button:nth-child(7)::before { content: "tune"; }

.tabitem {
    flex: 1 !important;
    min-width: 0 !important;
    padding: 20px 24px !important;
}

/* ── Pipeline steps ───────────────────────────────────────────────────── */
.pipeline-steps { display: flex; flex-direction: column; gap: 5px; padding: 2px 0; }
.pipeline-step {
    display: flex; align-items: center; gap: 10px;
    padding: 9px 14px; border-radius: var(--r-sm);
    border: 1px solid var(--_border); background: var(--_panel);
    font-size: 0.82rem; transition: border-color .2s, opacity .2s, background .2s;
}
.pipeline-step.pending  { opacity: .4; }
.pipeline-step.running  { border-color: var(--_accent); background: var(--_panel); }
.pipeline-step.done     { border-color: var(--_border); }
.pipeline-step.error    { border-color: var(--_danger); }
.ps-icon {
    font-family: 'Material Symbols Outlined'; font-style: normal;
    font-size: 18px; line-height: 1;
    width: 20px; text-align: center; flex-shrink: 0;
    color: var(--_muted);
}
.pipeline-step.pending  .ps-icon { color: var(--_muted); opacity: .5; }
.pipeline-step.running  .ps-icon { color: var(--_accent); animation: splash-spin 1.2s linear infinite; }
.pipeline-step.done     .ps-icon { color: var(--_accent); }
.pipeline-step.error    .ps-icon { color: var(--_danger); }
.ps-name   { flex: 1; color: var(--_text); font-weight: 500; }
.ps-detail { color: var(--_muted); font-size: 0.75rem; }

/* ── DataFrame / Event Table ─────────────────────────────────────────── */
#event-table table {
    background: var(--_panel) !important;
    border-collapse: collapse !important;
    border: 1px solid var(--_border) !important;
    border-radius: var(--r-sm) !important;
    overflow: hidden !important;
}
#event-table thead tr {
    background: rgba(255,255,255,.03) !important;
    border-bottom: 1px solid var(--_border) !important;
}
#event-table th {
    background: transparent !important;
    color: var(--_muted) !important;
    font-size: 0.6rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    padding: 6px 10px !important;
    line-height: 1.1 !important;
    border: none !important;
    white-space: nowrap !important;
    vertical-align: middle !important;
}
#event-table td {
    color: var(--_text) !important;
    font-size: 0.78rem !important;
    padding: 8px 10px !important;
    border: none !important;
    border-bottom: 1px solid var(--_border) !important;
    vertical-align: top !important;
}
#event-table tbody tr:last-child td { border-bottom: none !important; }
#event-table tbody tr:nth-child(even) td { background: rgba(255,255,255,.018) !important; }
#event-table tr:hover td { background: var(--_surface) !important; cursor: pointer !important; }
#event-table td:nth-child(1) { font-family: var(--font-mono) !important; font-size: 0.72rem !important; color: var(--_muted) !important; }
#event-table td:nth-child(4),
#event-table td:nth-child(5) { font-family: var(--font-mono) !important; font-size: 0.74rem !important; color: var(--_muted) !important; }
#event-table td:nth-child(2) { font-weight: 700 !important; color: var(--_accent) !important; }
#event-table td:nth-child(3) { max-width: 520px !important; white-space: normal !important; line-height: 1.35 !important; }
#event-table td:nth-child(7) { font-family: var(--font-mono) !important; font-size: 0.74rem !important; color: var(--_accent) !important; font-weight: 600 !important; }

/* Zone count numbers */
#count-entrance input, #count-counter input,
#count-back-door input, #count-aisles input {
    font-size: 2rem !important; font-weight: 700 !important;
    text-align: center !important; color: var(--_accent) !important;
    border-radius: var(--r-sm) !important;
}

/* Status output */
#status-box textarea { color: var(--_accent) !important; font-family: var(--font-mono) !important; font-size: 0.78rem !important; }

/* Section headings */
.block h3 {
    color: var(--_text) !important; font-size: .8rem !important;
    text-transform: uppercase !important; letter-spacing: .08em !important;
    border-bottom: 1px solid var(--_border); padding-bottom: 6px; margin-bottom: 10px;
}
.block em { color: var(--_muted) !important; }

/* Chatbot bubbles */
.message.user .bubble-wrap { background: var(--_panel)   !important; border-radius: var(--r-sm) var(--r-sm) var(--r-xs) var(--r-sm) !important; }
.message.bot  .bubble-wrap { background: var(--_surface) !important; border-radius: var(--r-sm) var(--r-sm) var(--r-sm) var(--r-xs) !important; }

/* Code blocks */
code, pre,
.prose code, .prose pre,
.message code, .message pre {
    background-color: var(--_panel) !important;
    color: var(--_text) !important;
    border: 1px solid var(--_border) !important;
    border-radius: var(--r-xs);
}
code { padding: 1px 5px; }
pre  { padding: 10px 14px !important; }
pre code { background-color: transparent !important; border: none !important; padding: 0 !important; }

/* Scrollbars */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--_panel); }
::-webkit-scrollbar-thumb { background: var(--_border); border-radius: var(--r-xs); }
::-webkit-scrollbar-thumb:hover { background: var(--_muted); }

/* ── Startup splash ───────────────────────────────────────────────────── */
#eyas-splash {
    position: fixed; inset: 0; z-index: 10000;
    background: var(--_bg, #1C1C1C);
    display: flex; flex-direction: column;
    align-items: center; justify-content: center; gap: 28px;
}
#eyas-splash.splash-fading {
    animation: splash-fade-out 0.65s ease forwards;
    pointer-events: none;
}
@keyframes splash-fade-out { to { opacity: 0; } }

.splash-logo-row { display: flex; align-items: center; gap: 12px; }
.splash-logo-dot {
    width: 10px; height: 10px; border-radius: 50%;
    background: var(--_accent); box-shadow: 0 0 12px var(--_accent);
    animation: splash-pulse 1.8s ease-in-out infinite;
}
@keyframes splash-pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(0.8); }
}
.splash-wordmark {
    font-family: var(--font-mono); font-size: 2.4rem; font-weight: 700;
    letter-spacing: 0.18em; color: var(--_accent);
}
.splash-subtitle {
    font-size: 0.78rem; color: var(--_muted); letter-spacing: 0.1em;
    text-transform: uppercase; margin-top: -20px;
}
.splash-card {
    background: var(--_panel);
    border: 1px solid var(--_border);
    border-radius: var(--r-card);
    padding: 0;
    min-width: 320px;
    overflow: hidden;
    box-shadow: var(--sh-lg);
}
.splash-card-header {
    font-family: var(--font-mono); font-size: 0.58rem; font-weight: 700;
    letter-spacing: 0.2em; text-transform: uppercase; color: var(--_muted);
    background: var(--_surface); border-bottom: 1px solid var(--_border);
    padding: 9px 18px;
}
.splash-item {
    display: flex; align-items: center; gap: 14px;
    padding: 13px 18px;
    border-bottom: 1px solid var(--_border);
}
.splash-item:last-child { border-bottom: none; }
.splash-item-icon {
    font-family: 'Material Symbols Outlined'; font-style: normal;
    font-size: 20px; line-height: 1; flex-shrink: 0;
    color: var(--_muted);
}
.splash-item-icon.si-loading { color: var(--_accent); animation: splash-spin 1.2s linear infinite; }
.splash-item-icon.si-ready   { color: #7DC47A; }
.splash-item-icon.si-error   { color: var(--_danger); }
.splash-item-icon.si-skipped { color: #C9904A; }
@keyframes splash-spin { to { transform: rotate(360deg); } }
.splash-item-body { display: flex; flex-direction: column; gap: 1px; }
.splash-item-label { font-size: 0.8rem; font-weight: 600; color: var(--_muted); text-transform: uppercase; letter-spacing: 0.04em; }
.splash-item-model { font-size: 0.9rem; font-weight: 500; color: var(--_text); }
.splash-item-detail { font-size: 0.72rem; color: var(--_muted); font-family: var(--font-mono); margin-top: 1px; }
.splash-progress-wrap {
    height: 3px; background: var(--_border); margin: 0;
    border-radius: 0 0 var(--r-card) var(--r-card); overflow: hidden;
}
.splash-progress-bar {
    height: 100%; background: var(--_accent);
    transition: width 0.5s ease;
    box-shadow: 0 0 6px var(--_accent);
}
"""


# Hawk Vision personality overrides
_HAWK_EXTRA_CSS = """
thead tr { border-bottom-color: var(--_border) !important; }
.tab-container button.selected { background: var(--_accent-a12) !important; }
tbody tr:nth-child(even) td { background: rgba(184,90,56,.04) !important; }
"""


def _build_css() -> str:
    p = _HAWK
    imports = (
        "@import url('https://fonts.googleapis.com/css2?"
        "family=Google+Sans:ital,wght@0,400;0,500;0,700;1,400"
        "&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400"
        "&display=swap');\n"
        "@import url('https://fonts.googleapis.com/css2?"
        "family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0');\n"
    )
    r, g, b = int(p["accent"][1:3], 16), int(p["accent"][3:5], 16), int(p["accent"][5:7], 16)
    root = (
        ":root {\n"
        f"    --_accent:     {p['accent']};\n"
        f"    --_accent-a12: rgba({r},{g},{b},0.12);\n"
        f"    --_accent-a08: rgba({r},{g},{b},0.08);\n"
        f"    --_panel:      {p['panel']};\n"
        f"    --_surface:    {p['surface']};\n"
        f"    --_bg:         {p['bg']};\n"
        f"    --_border:     {p['border']};\n"
        f"    --_text:       {p['text']};\n"
        f"    --_muted:      {p['muted']};\n"
        f"    --_danger:     {p['danger']};\n"
        "}\n"
    )
    return imports + root + _STRUCTURAL_CSS + _HAWK_EXTRA_CSS


# ---------------------------------------------------------------------------
# Font stacks
# ---------------------------------------------------------------------------

_FONTS_DEFAULT = [fonts.GoogleFont("Google Sans"), fonts.GoogleFont("DM Sans"), fonts.Font("system-ui"), fonts.Font("sans-serif")]
_FONTS_MONO    = [fonts.GoogleFont("JetBrains Mono"), fonts.Font("ui-monospace"), fonts.Font("Consolas"), fonts.Font("monospace")]


# ---------------------------------------------------------------------------
# Gradio theme — Hawk Vision, single fixed palette
# ---------------------------------------------------------------------------

class HawkTheme(Base):
    """Hawk-inspired surveillance console theme."""

    def __init__(self) -> None:
        p = _HAWK
        super().__init__(
            primary_hue=colors.orange,
            secondary_hue=colors.gray,
            neutral_hue=colors.gray,
            spacing_size=sizes.spacing_md,
            radius_size=sizes.radius_sm,
            text_size=sizes.text_sm,
            font=_FONTS_DEFAULT,
            font_mono=_FONTS_MONO,
        )
        super().set(
            # Page
            body_background_fill=p["bg"],          body_background_fill_dark=p["bg"],
            body_text_color=p["text"],              body_text_color_dark=p["text"],
            background_fill_primary=p["panel"],     background_fill_primary_dark=p["panel"],
            background_fill_secondary=p["surface"], background_fill_secondary_dark=p["surface"],
            # Blocks
            block_background_fill=p["panel"],       block_background_fill_dark=p["panel"],
            block_border_color=p["border"],         block_border_color_dark=p["border"],
            block_border_width="1px",
            block_label_text_color=p["label"],      block_label_text_color_dark=p["label"],
            block_label_background_fill=p["panel"], block_label_background_fill_dark=p["panel"],
            # Inputs — use panel (darker) so they read as inset against surface card bg
            input_background_fill=p["panel"],       input_background_fill_dark=p["panel"],
            input_border_color=p["border"],         input_border_color_dark=p["border"],
            input_border_color_focus=p["accent"],   input_border_color_focus_dark=p["accent"],
            input_placeholder_color=p["muted"],     input_placeholder_color_dark=p["muted"],
            # Primary button
            button_primary_background_fill=p["accent"],            button_primary_background_fill_dark=p["accent"],
            button_primary_background_fill_hover=p["accent_hover"], button_primary_background_fill_hover_dark=p["accent_hover"],
            button_primary_text_color="#ffffff",                   button_primary_text_color_dark="#ffffff",
            button_primary_border_color=p["accent"],               button_primary_border_color_dark=p["accent"],
            # Secondary button — tonal: accent-tinted fill, accent text
            button_secondary_background_fill=f"rgba({int(p['accent'][1:3],16)},{int(p['accent'][3:5],16)},{int(p['accent'][5:7],16)},.12)",
            button_secondary_background_fill_dark=f"rgba({int(p['accent'][1:3],16)},{int(p['accent'][3:5],16)},{int(p['accent'][5:7],16)},.12)",
            button_secondary_border_color="transparent",    button_secondary_border_color_dark="transparent",
            button_secondary_text_color=p["accent"],        button_secondary_text_color_dark=p["accent"],
            # Accent
            color_accent=p["accent"],
            color_accent_soft=f"rgba({int(p['accent'][1:3],16)},{int(p['accent'][3:5],16)},{int(p['accent'][5:7],16)},.18)",
        )
        self.name = "eyas-hawk"
        self.custom_css = _build_css()


_HAWK_THEME = HawkTheme()


# ---------------------------------------------------------------------------
# JS
# ---------------------------------------------------------------------------

_REC_JS = "(v) => { if (v) document.body.classList.add('has-feed'); else document.body.classList.remove('has-feed'); }"

# ---------------------------------------------------------------------------
# Static HTML
# ---------------------------------------------------------------------------

def _header_html(S: Strings) -> str:
    return f"""
<div class="eyas-title-row">
    <span class="eyas-rec">&#9679;&nbsp;REC</span>
    <span class="eyas-title">Eyas</span>
</div>
<div class="eyas-tagline">{S.t("header.tagline")}</div>
<p class="eyas-subtitle">
    {S.t("header.subtitle")}
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


_STEP_ICONS = {"pending": "radio_button_unchecked", "running": "sync", "done": "check_circle", "error": "error"}


def _splash_model_label(S: Strings, key: str, default: str) -> str:
    msg_key = SPLASH_MODEL_KEYS.get(key)
    return S.t(msg_key) if msg_key else default


def _steps_html(S: Strings, steps: list) -> str:
    rows = []
    for step_id, state, detail in steps:
        icon = _STEP_ICONS.get(state, "○")
        detail_span = f'<span class="ps-detail">{detail}</span>' if detail else ""
        rows.append(
            f'<div class="pipeline-step {state}">'
            f'<span class="ps-icon">{icon}</span>'
            f'<span class="ps-name">{S.pipeline_step_label(step_id)}</span>'
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
# Splash screen
# ---------------------------------------------------------------------------

def _splash_html(S: "Strings | None" = None, states: list | None = None, fading: bool = False) -> str:
    if S is None:
        S = Strings("en")
    _icon_class = {
        "waiting": ("hourglass_empty", ""),
        "loading": ("sync",            "si-loading"),
        "ready":   ("check_circle",    "si-ready"),
        "error":   ("error",           "si-error"),
        "skipped": ("warning",         "si-skipped"),
    }
    _detail_text = {
        "waiting": S.t("splash.waiting"),
        "loading": S.t("splash.loading"),
        "ready":   S.t("splash.ready"),
        "error":   S.t("splash.failed"),
        "skipped": S.t("splash.skipped"),
    }
    if states is None:
        from model_registry import get_states
        states = get_states()

    _registry_keys = ["yolo", "vlm", "llm", "tts", "tinyaya"]

    total = len(states)
    done_count = sum(1 for s in states if s.status in {"ready", "error", "skipped"})
    progress_pct = int(done_count / total * 100) if total else 0

    items_html = ""
    for i, s in enumerate(states):
        icon, cls = _icon_class.get(s.status, ("hourglass_empty", ""))
        detail = s.detail if s.detail else _detail_text.get(s.status, "")
        reg_key = _registry_keys[i] if i < len(_registry_keys) else ""
        label = _splash_model_label(S, reg_key, s.label)
        model_name = s.model_name or ""
        items_html += (
            f'<div class="splash-item">'
            f'<span class="splash-item-icon material-symbols-outlined {cls}">{icon}</span>'
            f'<div class="splash-item-body">'
            f'<span class="splash-item-label">{label}</span>'
            f'<span class="splash-item-model">{model_name}</span>'
            f'<span class="splash-item-detail">{detail}</span>'
            f'</div></div>'
        )

    fading_class = " splash-fading" if fading else ""
    return (
        f'<div id="eyas-splash" class="eyas-splash{fading_class}">'
        f'<div class="splash-logo-row">'
        f'<span class="splash-logo-dot"></span>'
        f'<span class="splash-wordmark">Eyas</span>'
        f'</div>'
        f'<div class="splash-subtitle">{S.t("header.tagline")}</div>'
        f'<div class="splash-card">'
        f'<div class="splash-card-header">{S.t("splash.initializing")}</div>'
        f'{items_html}'
        f'<div class="splash-progress-wrap">'
        f'<div class="splash-progress-bar" style="width:{progress_pct}%"></div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

def _load_prefs_file(prefs_path: Optional[Path]) -> dict:
    if prefs_path is None:
        return {}
    try:
        return json.loads(prefs_path.read_text())
    except Exception:
        return {}


def _save_prefs_file(prefs_path: Optional[Path], updates: dict) -> None:
    if prefs_path is None:
        return
    merged = {**_load_prefs_file(prefs_path), **updates}
    prefs_path.write_text(json.dumps(merged, indent=2))


def build_app(
    language: str = "en",
    prefs_path: Optional[Path] = None,
) -> gr.Blocks:

    S = Strings(language)

    with gr.Blocks(title=S.t("app.title")) as demo:

        # ── Startup splash (ComfyUI-style model loading screen) ──────────────
        splash_html  = gr.HTML(value=_splash_html(S), elem_id="splash-wrapper")
        splash_timer = gr.Timer(value=0.9, active=True)

        # ── Header ──────────────────────────────────────────────────────────
        with gr.Row():
            with gr.Column(scale=5, elem_id="eyas-header"):
                gr.HTML(_header_html(S))
            with gr.Column(scale=1, min_width=160, elem_id="theme-col"):
                gr.HTML(
                    f'<div class="eyas-theme-badge">'
                    f'Hawk Vision<br>'
                    f'{S.t("badge.language", language=LANGUAGE_LABELS.get(language, language))}'
                    f'</div>'
                )

        event_log_state: gr.State = gr.State([])
        output_dir_state: gr.State = gr.State("")

        # ── Main layout: sidebar + analysis panel ────────────────────────────
        with gr.Row():

            # — Left sidebar: input ──────────────────────────────────────────
            with gr.Column(scale=1, min_width=260, elem_id="eyas-sidebar"):
                gr.HTML(
                    '<div class="eyas-panel-header">'
                    '<span class="ph-dot"></span>'
                    f'<span class="ph-label">{S.t("header.footage")}</span>'
                    '</div>'
                )
                sample_dd = gr.Dropdown(
                    choices=list(_SAMPLE_PATHS.keys()),
                    label=S.t("labels.sample_clips"),
                    interactive=True,
                )
                load_sample_btn = gr.Button(S.t("buttons.load_sample"), variant="secondary", size="sm", elem_id="load-sample-btn")
                video_input = gr.Video(label=S.t("labels.original_video"), sources=["upload"])
                upload_status = gr.Textbox(label=S.t("labels.storage"), interactive=False, lines=1)

            # — Right panel: analysis + output ───────────────────────────────
            with gr.Column(scale=2, elem_id="eyas-main"):
                gr.HTML(
                    '<div class="eyas-panel-header">'
                    '<span class="ph-dot"></span>'
                    f'<span class="ph-label">{S.t("header.analysis")}</span>'
                    '</div>'
                )
                analyze_btn = gr.Button(
                    S.t("buttons.analyze"), variant="primary", size="lg", elem_id="analyze-btn",
                )
                status_box = gr.Textbox(
                    label=S.t("labels.status"), interactive=False, lines=1,
                    elem_id="status-box",
                )
                pipeline_html = gr.HTML(_steps_html(S, pipeline_steps_default()))
                annotated_img = gr.Image(label=S.t("labels.annotated_live"), interactive=False)
                annotated_vid = gr.Video(label=S.t("labels.annotated_video"), interactive=False, visible=False)

        video_input.change(fn=None, inputs=[video_input], js=_REC_JS)

        # ── Tabs ────────────────────────────────────────────────────────────
        with gr.Tabs(selected=0):

            with gr.TabItem(S.t("tabs.event_timeline")):
                with gr.Row():
                    _section_title(S.t("labels.detected_events"))
                    refresh_events_btn = gr.Button(
                        "", variant="secondary", size="sm",
                        elem_id="refresh-events-btn", scale=0, min_width=40,
                    )
                event_table = gr.DataFrame(
                    headers=S.table_headers(),
                    label=S.t("labels.event_log"), interactive=False, wrap=True, elem_id="event-table",
                )
                with gr.Row():
                    with gr.Column(scale=2):
                        clip_selector = gr.Dropdown(label=S.t("labels.select_clip"), choices=[], interactive=True)
                    with gr.Column(scale=3):
                        clip_preview = _clip_video(S.t("labels.clip_preview"))

            with gr.TabItem(S.t("tabs.summary_alerts")):
                with gr.Row():
                    with gr.Column():
                        _section_title(S.t("labels.ai_summary"))
                        summary_box = gr.Textbox(label=S.t("labels.overnight_summary"), lines=6, interactive=False)
                        summary_translation_time = gr.Textbox(
                            label=S.t("labels.translation_time"), interactive=False, lines=1,
                        )
                        risk_badge  = gr.Label(label=S.t("labels.risk_level"))
                    with gr.Column():
                        _section_title(S.t("labels.flagged_items"))
                        flags_box = gr.JSON(label=S.t("labels.flags"))
                        suspicious_clips_dd = gr.Dropdown(
                            label=S.t("labels.suspicious_clips"), choices=[], interactive=True,
                        )
                        flagged_clip_preview = _clip_video(S.t("labels.flagged_clip_preview"))

            with gr.TabItem(S.t("tabs.ask_footage")):
                _section_title(S.t("labels.ask_question"))
                gr.Markdown(S.t("labels.ask_examples"))
                chatbot = gr.Chatbot(label=S.t("labels.footage_qa"), height=420)
                qa_translation_time = gr.Textbox(
                    label=S.t("labels.translation_time"), interactive=False, lines=1,
                )
                with gr.Row():
                    query_input = gr.Textbox(
                        placeholder=S.t("labels.question_placeholder"),
                        label=S.t("labels.your_question"), scale=5, lines=1,
                    )
                    ask_btn = gr.Button(S.t("buttons.ask"), variant="primary", scale=1)
                clear_btn = gr.Button(S.t("buttons.clear_chat"), variant="secondary", size="sm")

            with gr.TabItem(S.t("tabs.detection_metrics")):
                _section_title(S.t("labels.zone_counts"))
                with gr.Row():
                    count_entrance  = _zone_number(S.zone_label("entrance"),  "count-entrance")
                    count_counter   = _zone_number(S.zone_label("counter"),   "count-counter")
                    count_back_door = _zone_number(S.zone_label("back_door"), "count-back-door")
                    count_aisles    = _zone_number(S.zone_label("aisles"),    "count-aisles")
                metrics_json = gr.JSON(label=S.t("labels.raw_counts"))

            with gr.TabItem(S.t("tabs.audio_report")):
                _section_title(S.t("labels.spoken_report"))
                gr.Markdown(S.t("labels.audio_help"))
                audio_output       = gr.Audio(label=S.t("labels.tts_report"), interactive=False)
                audio_status       = gr.Textbox(label=S.t("labels.status"), interactive=False, lines=1)
                generate_audio_btn = gr.Button(S.t("buttons.generate_audio"), variant="secondary")

            # ── Clip Library ─────────────────────────────────────────────────
            with gr.TabItem(S.t("tabs.clip_library")):
                _section_title(S.t("labels.stored_clips"))
                with gr.Row():
                    refresh_lib_btn = gr.Button(S.t("buttons.refresh"), size="sm", variant="secondary")
                    lib_dd = gr.Dropdown(
                        label=S.t("labels.clips"), choices=storage.choices(language), interactive=True, scale=4,
                    )
                    load_clip_btn   = gr.Button(S.t("buttons.load_for_analysis"), variant="primary", size="sm", scale=1)
                    delete_clip_btn = gr.Button(S.t("buttons.delete"), variant="stop", size="sm", scale=1)

                lib_status   = gr.Textbox(label=S.t("labels.status"), interactive=False, lines=1)
                lib_preview  = gr.Video(label=S.t("labels.preview"), interactive=False)

            with gr.TabItem(S.t("tabs.settings")):
                _section_title(S.t("labels.language"))
                gr.Markdown(S.t("labels.language_help"))
                language_dd = gr.Dropdown(
                    choices=list(LANGUAGE_LABELS.values()),
                    value=LANGUAGE_LABELS.get(language, LANGUAGE_LABELS["en"]),
                    label=S.t("labels.language"),
                    interactive=True,
                )
                save_lang_btn = gr.Button(S.t("buttons.save_language"), variant="secondary", size="sm")
                lang_status = gr.Markdown("")

        # ── Callbacks ───────────────────────────────────────────────────────

        # Shared live-event state — written by the pipeline thread, read by the refresh button
        _live_events: list = []
        _live_rows: list = []

        def _event_clip_choices(evs: list) -> list:
            choices = []
            for i, ev in enumerate(evs):
                t = ev.get("timestamp") or 0
                activity = "pickup" if ev.get("pickup_confirmed") else (ev.get("activity") or "observation")
                choices.append(f"#{i} – {activity[:25]} @ {t:.1f}s")
            return choices

        _CLIPS_DIR = str(Path(__file__).parent.parent / "data" / "clips")

        _INPUTS_DIR = str(Path(__file__).parent.parent / "input")

        # Upload → auto-store (skip clips-dir and built-in sample files)
        def on_upload(video_path):
            if video_path is None:
                return ""
            norm = video_path.replace("\\", "/")
            if _CLIPS_DIR.replace("\\", "/") in norm:
                return S.t("status.clip_from_library")
            if _INPUTS_DIR.replace("\\", "/") in norm:
                return S.t("status.sample_not_stored")
            try:
                entry = storage.store(video_path, source="upload")
                return S.t("status.stored", filename=entry["filename"], size_mb=entry["size_mb"])
            except Exception as exc:
                return S.t("status.storage_error", error=exc)

        video_input.change(on_upload, inputs=[video_input], outputs=[upload_status])

        def load_sample(name: str):
            return _SAMPLE_PATHS.get(name)

        load_sample_btn.click(load_sample, inputs=[sample_dd], outputs=[video_input])

        # ── Splash timer — polls model registry, fades splash when ready ──────
        def _poll_splash():
            done = _mreg.all_done()
            return _splash_html(S, fading=done), gr.update(active=not done)

        splash_timer.tick(_poll_splash, outputs=[splash_html, splash_timer])

        def run_pipeline(video_path):
            import tempfile
            import time as _time
            import cv2 as _cv2
            from visual_pipeline import run_visual_pipeline

            def _summarize(events):
                _r = _mreg.get("llm")
                if _r is None:
                    raise RuntimeError("LLM not available")
                return _r.summarize_events(events)

            steps = pipeline_steps_default()  # mutable copy
            step_start: dict = {}
            _last_frame: list = [None]  # latest annotated frame (RGB numpy array)
            from postprocessing.translate_tts import TranslateStats

            text_cache: dict[str, str] = {}
            translation_stats = TranslateStats()
            _live_events.clear()
            _live_rows.clear()

            def emit(status):
                f = _last_frame[0]
                ann = gr.update(value=f, visible=f is not None) if f is not None else gr.update(visible=False)
                return (
                    _steps_html(S, _annotate_elapsed(steps, step_start)), status,
                    list(_live_events), list(_live_rows), gr.update(choices=[]), "", "", {"none": 1.0},
                    [], gr.update(choices=[]), {}, 0, 0, 0, 0,
                    ann,
                    gr.update(visible=False),
                    "",
                )

            def _start_step(idx: int, step_id: str, detail: str = "") -> None:
                step_start[idx] = _time.time()
                steps[idx] = (step_id, "running", detail)

            def _finish_step(idx: int, step_id: str, detail: str = "") -> None:
                step_start.pop(idx, None)
                steps[idx] = (step_id, "done", detail)

            if video_path is None:
                steps[0] = ("load_video", "error", S.t("status.no_video_selected"))
                yield emit(S.t("status.no_video"))
                return

            # ── Step 1: load ────────────────────────────────────────────────
            _start_step(0, "load_video")
            yield emit(S.t("status.loading_video"))

            _finish_step(0, "load_video", Path(video_path).name)
            _start_step(1, "yolo", S.t("pipeline.starting"))
            steps[2] = ("vlm", "pending", "")
            yield emit(S.t("status.running_yolo"))

            # ── Step 2: visual pipeline (threaded so progress yields work) ───
            import queue as _queue
            import threading as _threading

            output_dir = tempfile.mkdtemp(prefix="eyas_out_")
            _q: _queue.Queue = _queue.Queue()

            _last_progress_t = [0.0]
            def _on_progress(done: int, total: int, track_count: int, vlm_fired: bool, annotated_frame=None) -> None:
                now = _time.time()
                if vlm_fired or now - _last_progress_t[0] >= 0.2:
                    display_frame = None
                    if annotated_frame is not None:
                        h, w = annotated_frame.shape[:2]
                        if w > 640:
                            display_frame = _cv2.resize(annotated_frame, (640, int(h * 640 / w)))
                        else:
                            display_frame = annotated_frame.copy()
                        display_frame = _cv2.cvtColor(display_frame, _cv2.COLOR_BGR2RGB)
                    _q.put(("progress", done, total, track_count, vlm_fired, display_frame))
                    _last_progress_t[0] = now

            def _on_new_events(evs: list) -> None:
                for ev in evs:
                    i = len(_live_events)
                    _live_events.append(ev)
                    row = format_event_row(
                        ev, i, S, text_cache=text_cache, stats=translation_stats,
                    )
                    _live_rows.append(row)
                    ev_kind = "pickup" if ev.get("pickup_confirmed") else "observation"
                    activity = (ev.get("activity") or "").strip() or "—"
                    print(
                        f"[EVENT #{i}] {fmt_event_time(ev.get('timestamp'))} | "
                        f"{ev_kind.upper()} | zone={ev.get('zone') or '?'} | "
                        f"{activity[:100]}"
                    )

            def _run() -> None:
                try:
                    result = run_visual_pipeline(
                        video_path=video_path,
                        output_dir=output_dir,
                        write_annotated_video=True,
                        progress=_on_progress,
                        on_event=_on_new_events,
                        preloaded_tracker=_mreg.get("yolo"),
                        preloaded_vlm=_mreg.get("vlm"),
                        locale=language,
                    )
                    _q.put(("done", result))
                except Exception as exc:
                    _q.put(("error", f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"))

            _threading.Thread(target=_run, daemon=True).start()

            vp = None
            _model_loaded = False
            while True:
                try:
                    msg = _q.get(timeout=1.0)
                except _queue.Empty:
                    # Still in model-load phase — pulse the detail so the user knows
                    if not _model_loaded:
                        steps[1] = ("yolo", "running", S.t("pipeline.loading_weights"))
                        steps[2] = ("vlm", "running", S.t("pipeline.loading_weights"))
                        yield emit(S.t("status.loading_models"))
                    else:
                        # Already processing — re-yield to refresh elapsed timers
                        yield emit(S.t("status.processing"))
                    continue

                kind = msg[0]
                if kind == "progress":
                    if not _model_loaded:
                        _model_loaded = True
                        step_start[1] = _time.time()
                    _, done, total, track_count, vlm_fired, display_frame = msg
                    if display_frame is not None:
                        _last_frame[0] = display_frame
                    pct = f"{done}/{total}" if total else str(done)
                    person_key = "pipeline.persons" if track_count == 1 else "pipeline.persons_plural"
                    person_s = S.t(person_key, count=track_count)
                    steps[1] = ("yolo", "running", f"{S.t('pipeline.frame', pct=pct)} · {person_s}")
                    if vlm_fired:
                        if 2 not in step_start:
                            step_start[2] = _time.time()
                        steps[2] = ("vlm", "running", S.t("pipeline.frame", pct=pct))
                    yield emit(S.t("status.processing_frame", pct=pct))
                elif kind == "done":
                    vp = msg[1]
                    break
                else:
                    steps[1] = ("yolo", "error", str(msg[1])[:80])
                    steps[2] = ("vlm", "error", "")
                    yield emit(S.t("status.pipeline_error", error=msg[1]))
                    return

            events: List[Dict] = vp.events
            _finish_step(1, "yolo",
                         S.t("pipeline.frames_tracks", frames=vp.frames_processed, tracks=vp.unique_tracks))
            _finish_step(2, "vlm", S.t("pipeline.events_count", count=len(events)))
            _start_step(3, "llm_summarize")

            rows = [
                format_event_row(ev, i, S, text_cache=text_cache, stats=translation_stats)
                for i, ev in enumerate(events)
            ]
            _live_rows.clear()
            _live_rows.extend(rows)

            zone_counts = {"entrance": 0, "counter": 0, "back_door": 0, "aisles": 0}
            for ev in events:
                z = ev.get("zone", "").lower().replace(" ", "_")
                if z in zone_counts:
                    zone_counts[z] += 1

            f = _last_frame[0]
            yield (
                _steps_html(S, _annotate_elapsed(steps, step_start)), S.t("status.running_llm"),
                events, rows, gr.update(choices=[]),
                "", "", {"none": 1.0}, [], gr.update(choices=[]),
                zone_counts,
                zone_counts["entrance"], zone_counts["counter"],
                zone_counts["back_door"], zone_counts["aisles"],
                gr.update(value=f, visible=f is not None) if f is not None else gr.update(visible=False),
                gr.update(visible=False),
                output_dir,
            )

            # ── Step 3: LLM ─────────────────────────────────────────────────
            try:
                llm = _summarize(events)
            except Exception:
                llm = {"summary": S.t("status.llm_unavailable"),
                       "flags": [], "suspicious_clips": [], "risk_level": "none"}

            llm_display, llm_stats = localize_llm_result(llm, language)

            combined_stats = translation_stats
            if llm_stats:
                combined_stats = combined_stats.merge(llm_stats)
            translation_time_str = format_translation_time(
                S,
                combined_stats if (combined_stats.cache_hits or combined_stats.cache_misses) else None,
            )

            risk_key = llm.get("risk_level", "none")
            _finish_step(3, "llm_summarize", S.t("pipeline.risk", level=S.risk_label(risk_key)))
            status = S.t(
                "status.done",
                frames=vp.frames_processed,
                tracks=vp.unique_tracks,
                events=len(events),
            )
            if translation_time_str:
                status = f"{status}  ·  {translation_time_str}"
            ann_vid_path = vp.annotated_video_path
            yield (
                _steps_html(S, _annotate_elapsed(steps, step_start)), status,
                events, rows, gr.update(choices=_event_clip_choices(events), value=None),
                llm_display["summary"], translation_time_str,
                {S.risk_label(risk_key): 1.0},
                llm_display["flags"], gr.update(choices=llm["suspicious_clips"]),
                zone_counts,
                zone_counts["entrance"], zone_counts["counter"],
                zone_counts["back_door"], zone_counts["aisles"],
                gr.update(visible=False),
                gr.update(value=ann_vid_path, visible=ann_vid_path is not None),
                output_dir,
            )

        analyze_btn.click(
            run_pipeline,
            inputs=[video_input],
            outputs=[
                pipeline_html, status_box,
                event_log_state, event_table, clip_selector,
                summary_box, summary_translation_time, risk_badge, flags_box, suspicious_clips_dd,
                metrics_json, count_entrance, count_counter, count_back_door, count_aisles,
                annotated_img, annotated_vid,
                output_dir_state,
            ],
        )

        def _load_clip(clip_name: str, out_dir: str):
            if not clip_name or not out_dir:
                return gr.update()
            p = Path(out_dir) / clip_name
            if p.is_file():
                return gr.update(value=str(p), visible=True)
            # Clip file not extracted — show annotated video as fallback
            ann = Path(out_dir) / next(
                (f for f in Path(out_dir).iterdir() if f.suffix == ".mp4"), Path()
            )
            return gr.update(value=str(ann) if ann.exists() else None, visible=ann.exists())

        def _refresh_events():
            return list(_live_events), list(_live_rows)

        refresh_events_btn.click(_refresh_events, outputs=[event_log_state, event_table])

        clip_selector.change(_load_clip, inputs=[clip_selector, output_dir_state], outputs=[clip_preview])
        suspicious_clips_dd.change(_load_clip, inputs=[suspicious_clips_dd, output_dir_state], outputs=[flagged_clip_preview])

        def ask_footage(message: str, history: list, events: List[Dict]):
            def _append_turn(hist: list, user_msg: str, assistant_msg: str) -> list:
                return hist + [
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": assistant_msg},
                ]

            if not message.strip():
                return history, "", ""
            if not events:
                reply = S.t("status.no_events_qa")
                return _append_turn(history, message, reply), "", ""
            try:
                _r = _mreg.get("llm")
                if _r is None:
                    reply = S.t("status.llm_unavailable")
                    return _append_turn(history, message, reply), "", ""
                result = _r.answer_query(events, message)
                reply = result["answer"]
                reply, stats = localize_text(reply, language)
                if result.get("clips"):
                    reply += "\n\n" + S.t("status.related_clips", clips=", ".join(result["clips"]))
                timing = format_translation_time(S, stats)
            except Exception as exc:
                reply = S.t("status.llm_error", error=f"{type(exc).__name__}: {exc}")
                timing = ""
            return _append_turn(history, message, reply), "", timing

        ask_btn.click(
            ask_footage,
            inputs=[query_input, chatbot, event_log_state],
            outputs=[chatbot, query_input, qa_translation_time],
        )
        query_input.submit(
            ask_footage,
            inputs=[query_input, chatbot, event_log_state],
            outputs=[chatbot, query_input, qa_translation_time],
        )
        clear_btn.click(lambda: ([], "", ""), outputs=[chatbot, query_input, qa_translation_time])

        def generate_audio(events: List[Dict]):
            if not events:
                return None, S.t("status.no_events_qa")
            _r = _mreg.get("llm")
            if _r is None:
                return None, S.t("status.llm_unavailable")
            try:
                llm = _r.summarize_events(events)
                text = llm.get("summary", "").strip()
                if not text:
                    return None, "No summary to speak."
                text, stats = localize_text(text, language)
                from postprocessing.translate_tts import tts
                import numpy as np
                chunks = list(tts(text, target_lang=S.tts_lang))
                if not chunks:
                    return None, "TTS produced no audio."
                sample_rate = chunks[0][0]
                audio = np.concatenate([c[1] for c in chunks])
                timing = format_translation_time(S, stats)
                return (sample_rate, audio), timing or "Done."
            except Exception as exc:
                return None, f"Audio error: {type(exc).__name__}: {exc}"

        generate_audio_btn.click(
            generate_audio,
            inputs=[event_log_state],
            outputs=[audio_output, audio_status],
        )

        # ── Clip Library callbacks ───────────────────────────────────────────

        def refresh_library():
            return gr.update(choices=storage.choices(language))

        def preview_clip(choice: str):
            path = storage.path_from_choice(choice) if choice else None
            return path

        def load_for_analysis(choice: str):
            path = storage.path_from_choice(choice) if choice else None
            if path is None:
                return None, S.t("status.clip_not_found")
            return path, S.t("status.loaded_clip", choice=choice)

        def delete_clip(choice: str):
            if not choice:
                return S.t("status.nothing_selected"), gr.update(choices=storage.choices(language))
            filename = choice.split(" — ", 1)[1].split("  ")[0].strip() if " — " in choice else ""
            ok = storage.delete(filename) if filename else False
            msg = S.t("status.deleted", filename=filename) if ok else S.t("status.delete_failed")
            return msg, gr.update(choices=storage.choices(language))

        refresh_lib_btn.click(refresh_library, outputs=[lib_dd])
        lib_dd.change(preview_clip, inputs=[lib_dd], outputs=[lib_preview])
        load_clip_btn.click(load_for_analysis, inputs=[lib_dd], outputs=[video_input, lib_status])
        delete_clip_btn.click(delete_clip, inputs=[lib_dd], outputs=[lib_status, lib_dd])

        def save_language(lang_label: str) -> str:
            if prefs_path is None:
                return S.t("status.no_prefs_path")
            lang_key = next((k for k, v in LANGUAGE_LABELS.items() if v == lang_label), None)
            if lang_key is None:
                lang_key = lang_label if lang_label in LANGUAGE_LABELS else "en"
            try:
                _save_prefs_file(prefs_path, {"language": lang_key})
                return S.t("status.language_saved", language=lang_label)
            except Exception as exc:
                return S.t("status.prefs_error", error=exc)

        save_lang_btn.click(save_language, inputs=[language_dd], outputs=[lang_status])

    return demo, _HAWK_THEME
