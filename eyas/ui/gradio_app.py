"""Gradio UI for Eyas — AI Security Camera Agent.

Theme is selected at startup (via preferences.json / CLI) and baked into
the Gradio theme object.  No runtime CSS class-toggling; restart to change.
"""

import json
import traceback
from pathlib import Path
from typing import Dict, List, Optional

import gradio as gr
from gradio.themes.base import Base
from gradio.themes.utils import colors, fonts, sizes

from storage import manager as storage
from streaming.capture import default_capture as _stream
import model_registry as _mreg

_mreg.start()

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

/* ── Card panels ─────────────────────────────────────────────────────── */
#eyas-sidebar {
    background: var(--_panel) !important;
    border: 1px solid var(--_border) !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 16px rgba(0,0,0,.35) !important;
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
    border-radius: 12px !important;
    box-shadow: 0 4px 16px rgba(0,0,0,.35) !important;
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

/* Re-style inputs/selects/textareas inside the cards so they still look distinct */
#eyas-sidebar input, #eyas-sidebar textarea, #eyas-sidebar select,
#eyas-main    input, #eyas-main    textarea, #eyas-main    select {
    background: var(--_surface) !important;
    border: 1px solid var(--_border) !important;
    border-radius: 6px !important;
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
    background: var(--_surface);
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

/* ── Material Design 3 buttons ───────────────────────────────────────── */
/* All primary buttons: filled pill */
button.primary, button[data-testid="primary"] {
    border-radius: 20px !important;
}
/* All secondary buttons: outlined pill */
button.secondary, button[data-testid="secondary"] {
    border-radius: 20px !important;
}

/* Analyze button: full-width pill, Material icon, physical press */
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
    border-radius: 20px !important;
    width: 100% !important;
    margin: 0 !important;
    transition: transform 0.08s ease, box-shadow 0.08s ease !important;
    box-shadow: 0 4px 0 rgba(0,0,0,.5), 0 1px 3px rgba(0,0,0,.3) !important;
    transform: translateY(0) !important;
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
    transform: translateY(-3px) !important;
    box-shadow: 0 7px 0 rgba(0,0,0,.5), 0 2px 8px rgba(0,0,0,.3) !important;
}
#analyze-btn:active {
    transform: translateY(2px) !important;
    box-shadow: 0 1px 0 rgba(0,0,0,.5) !important;
}

/* ── Sidebar navigation tabs ─────────────────────────────────────────── */

/* Outer container: horizontal flex — nav left, content right */
.tabs {
    display: flex !important;
    flex-direction: row !important;
    align-items: stretch !important;
    gap: 0 !important;
    background: var(--_panel) !important;
    border: 1px solid var(--_border) !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 16px rgba(0,0,0,.3) !important;
    overflow: hidden !important;
}

/* Left sidebar strip that wraps .tab-container */
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

/* Hide Gradio's horizontal-scroll duplicate + overflow "…" button */
.tab-container.visually-hidden { display: none !important; }
.overflow-menu { display: none !important; }

/* The actual list of nav buttons */
.tab-container {
    display: flex !important;
    flex-direction: column !important;
    height: auto !important;
    overflow: visible !important;
    gap: 1px !important;
    border: none !important;
    width: 100% !important;
}

/* Nav buttons — MD3 navigation rail/drawer style */
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
    border-radius: 28px !important;
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
.tab-container button[aria-selected="true"]::after {
    display: none !important;
    content: none !important;
}
.tab-container button:focus, .tab-container button:focus-visible {
    outline: none !important;
    box-shadow: none !important;
}

/* Material Symbol icons via ::before */
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
.tab-container button:nth-child(6)::before { content: "videocam"; }
.tab-container button:nth-child(7)::before { content: "video_library"; }
.tab-container button:nth-child(8)::before { content: "tune"; }

/* Tab content panel fills remaining width */
.tabitem {
    flex: 1 !important;
    min-width: 0 !important;
    padding: 20px 24px !important;
}

/* ── Pipeline steps ───────────────────────────────────────────────────── */
.pipeline-steps { display: flex; flex-direction: column; gap: 5px; padding: 2px 0; }
.pipeline-step {
    display: flex; align-items: center; gap: 10px;
    padding: 9px 14px; border-radius: 7px;
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

/* ── Refresh events icon button ──────────────────────────────────────── */
#refresh-events-btn {
    padding: 5px 8px !important;
    min-width: 34px !important;
    max-width: 34px !important;
    border-radius: 8px !important;
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


/* ── DataFrame / Event Table ─────────────────────────────────────────── */
#event-table table {
    background: var(--_panel) !important;
    border-collapse: collapse !important;
    border: 1px solid var(--_border) !important;
    border-radius: 10px !important;
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
/* index + time columns: monospace muted */
#event-table td:nth-child(1) { font-family: var(--font-mono) !important; font-size: 0.72rem !important; color: var(--_muted) !important; }
#event-table td:nth-child(4),
#event-table td:nth-child(5) { font-family: var(--font-mono) !important; font-size: 0.74rem !important; color: var(--_muted) !important; }
#event-table td:nth-child(2) { font-weight: 700 !important; color: var(--_accent) !important; }
#event-table td:nth-child(3) {
    max-width: 520px !important;
    white-space: normal !important;
    line-height: 1.35 !important;
}
#event-table td:nth-child(7) { font-family: var(--font-mono) !important; font-size: 0.74rem !important; color: var(--_accent) !important; font-weight: 600 !important; }

/* Zone count numbers */
#count-entrance input, #count-counter input,
#count-back-door input, #count-aisles input {
    font-size: 2rem !important; font-weight: 700 !important;
    text-align: center !important; color: var(--_accent) !important;
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
.message.user .bubble-wrap { background: var(--_panel)   !important; border-radius: 8px 8px 2px 8px !important; }
.message.bot  .bubble-wrap { background: var(--_surface) !important; border-radius: 8px 8px 8px 2px !important; }

/* Code blocks */
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

/* ── Startup splash screen ───────────────────────────────────────────── */
#eyas-splash {
    position: fixed; inset: 0; z-index: 10000;
    background: var(--_bg, #0a0e17);
    display: flex; flex-direction: column;
    align-items: center; justify-content: center; gap: 28px;
}
#eyas-splash.splash-fading {
    animation: splash-fade-out 0.65s ease forwards;
    pointer-events: none;
}
@keyframes splash-fade-out { to { opacity: 0; } }

.splash-logo-row {
    display: flex; align-items: center; gap: 12px;
}
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
    border-radius: 16px;
    padding: 0;
    min-width: 320px;
    overflow: hidden;
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
.splash-item-icon.si-loading {
    color: var(--_accent);
    animation: splash-spin 1.2s linear infinite;
}
.splash-item-icon.si-ready   { color: #10b981; }
.splash-item-icon.si-error   { color: var(--_danger); }
.splash-item-icon.si-skipped { color: #f59e0b; }
@keyframes splash-spin { to { transform: rotate(360deg); } }
.splash-item-body { display: flex; flex-direction: column; gap: 2px; }
.splash-item-label { font-size: 0.85rem; font-weight: 500; color: var(--_text); }
.splash-item-detail { font-size: 0.72rem; color: var(--_muted); font-family: var(--font-mono); }
.splash-progress-wrap {
    height: 3px; background: var(--_border); margin: 0;
    border-radius: 0 0 16px 16px; overflow: hidden;
}
.splash-progress-bar {
    height: 100%; background: var(--_accent);
    transition: width 0.5s ease;
    box-shadow: 0 0 6px var(--_accent);
}
"""


# Per-theme personality overrides — appended after _STRUCTURAL_CSS at build time.
# Only the active theme's block is included; no runtime selectors needed.
_PER_THEME_CSS: Dict[str, str] = {
    "night": """
/* Night Vision: terminal green glow */
thead tr { border-bottom-color: var(--_accent) !important; }
th { text-shadow: 0 0 10px rgba(16,185,129,.35) !important; }
.tab-container button.selected { background: rgba(16,185,129,.07) !important; }
.eyas-panel-header .ph-label { letter-spacing: 0.22em !important; }
""",
    "amber": """
/* Amber CRT: warm retro terminal */
table { font-family: var(--font-mono) !important; }
th { letter-spacing: 0.18em !important; }
.tabs, #eyas-sidebar, #eyas-main { border-radius: 6px !important; }
tbody tr:nth-child(even) td { background: rgba(245,158,11,.05) !important; }
.eyas-panel-header { letter-spacing: 0.25em !important; }
""",
    "cyber": """
/* Cyberpunk: neon glow */
th { text-shadow: 0 0 14px var(--_accent) !important; }
thead tr { border-bottom-color: var(--_accent) !important; box-shadow: 0 2px 14px rgba(168,85,247,.25) !important; }
.tab-container button.selected { text-shadow: 0 0 8px var(--_accent) !important; }
.tabs, #eyas-sidebar, #eyas-main { border-radius: 4px !important; }
.pipeline-step.running { box-shadow: 0 0 12px rgba(168,85,247,.4) !important; }
tbody tr:nth-child(even) td { background: rgba(168,85,247,.04) !important; }
""",
    "sentinel": """
/* Sentinel: clean enterprise blue */
thead tr { border-bottom: 2px solid var(--_accent) !important; }
.tab-container button.selected { font-weight: 600 !important; }
#analyze-btn { border-radius: 4px !important; }
tbody tr:nth-child(even) td { background: rgba(59,130,246,.04) !important; }
""",
    "voltagent": """
/* VoltAgent: minimal green terminal */
th { text-shadow: 0 0 8px rgba(0,217,146,.25) !important; }
thead tr { border-bottom-color: var(--_accent) !important; }
.tab-container button.selected { background: rgba(0,217,146,.05) !important; }
""",
    "xai": """
/* xAI: bold orange-tech */
thead tr { border-bottom: 2px solid var(--_accent) !important; }
th { font-weight: 800 !important; font-size: 0.68rem !important; }
.tabs, #eyas-sidebar, #eyas-main { border-radius: 6px !important; }
""",
    "warp": """
/* Warp: warm rounded terminal */
.tabs, #eyas-sidebar, #eyas-main { border-radius: 10px !important; }
th { letter-spacing: 0.08em !important; font-weight: 600 !important; color: var(--_text) !important; text-transform: none !important; }
thead tr { background: rgba(247,245,240,.05) !important; }
tbody tr:nth-child(even) td { background: rgba(247,245,240,.025) !important; }
""",
    "linear": """
/* Linear: ultra minimal */
.tabs, #eyas-sidebar, #eyas-main { box-shadow: none !important; }
th { font-weight: 500 !important; color: var(--_muted) !important; letter-spacing: 0.06em !important; }
thead tr { background: transparent !important; }
.tab-container button { font-size: 0.8rem !important; }
""",
    "sentry": """
/* Sentry: lime-on-purple drama */
th { text-shadow: 0 0 10px rgba(194,239,78,.3) !important; }
thead tr { border-bottom-color: var(--_accent) !important; }
.tab-container button.selected { background: rgba(194,239,78,.07) !important; }
tbody tr:nth-child(even) td { background: rgba(194,239,78,.03) !important; }
""",
    "stripe": """
/* Stripe: gradient-header indigo */
thead tr { background: linear-gradient(135deg, var(--_surface) 0%, rgba(83,58,253,.18) 100%) !important; border-bottom: 1px solid var(--_accent) !important; }
th { font-weight: 700 !important; }
.tabs, #eyas-sidebar, #eyas-main { border-radius: 8px !important; }
""",
    "supabase": """
/* Supabase: clean dark green */
thead tr { border-bottom: 1px solid var(--_accent) !important; }
th { font-size: 0.64rem !important; letter-spacing: 0.13em !important; }
tbody tr:nth-child(even) td { background: rgba(62,207,142,.03) !important; }
""",
    "vercel": """
/* Vercel: pure minimal black */
.tabs, #eyas-sidebar, #eyas-main { border-radius: 0 !important; border-color: #333 !important; }
th { color: var(--_accent) !important; font-weight: 600 !important; font-size: 0.65rem !important; letter-spacing: 0.06em !important; }
thead tr { border-bottom: 1px solid #333 !important; }
.tab-container button.selected { background: rgba(0,112,243,.06) !important; }
tbody tr:nth-child(even) td { background: rgba(255,255,255,.03) !important; }
""",
    "cursor": """
/* Cursor: mac-like warm light */
.tabs, #eyas-sidebar, #eyas-main { border-radius: 10px !important; box-shadow: 0 2px 8px rgba(0,0,0,.07) !important; }
th { color: var(--_muted) !important; font-weight: 600 !important; font-size: 0.64rem !important; }
thead tr { border-bottom: 1px solid var(--_border) !important; }
tbody tr:nth-child(even) td { background: rgba(0,0,0,.02) !important; }
""",
    "runway": """
/* Runway: typographic serif elegance */
th { font-family: var(--font) !important; font-style: italic !important; color: var(--_muted) !important; font-size: 0.76rem !important; letter-spacing: 0.02em !important; text-transform: none !important; }
.tabs, #eyas-sidebar, #eyas-main { border-radius: 2px !important; box-shadow: none !important; }
.tab-container button { letter-spacing: 0.02em !important; }
""",
}


def _build_css(p: dict, theme_key: str = "night") -> str:
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
    return imports + root + _STRUCTURAL_CSS + _PER_THEME_CSS.get(theme_key, "")


# ---------------------------------------------------------------------------
# Per-theme font stacks
# ---------------------------------------------------------------------------

_GS = [fonts.GoogleFont("Google Sans"), fonts.GoogleFont("DM Sans"), fonts.Font("system-ui"), fonts.Font("sans-serif")]

_FONTS: Dict[str, list] = {
    # Simple themes
    "night":    _GS,
    "amber":    _GS,
    "cyber":    _GS,
    "sentinel": _GS,
    # Advanced themes
    "voltagent": _GS,
    "xai":       _GS,
    "warp":      _GS,
    "linear":    _GS,
    "sentry":    [fonts.GoogleFont("Google Sans"), fonts.GoogleFont("Rubik"), fonts.Font("system-ui"), fonts.Font("sans-serif")],
    "stripe":    _GS,
    "supabase":  _GS,
    "vercel":    [fonts.GoogleFont("Google Sans"), fonts.GoogleFont("Geist"), fonts.Font("system-ui"), fonts.Font("sans-serif")],
    "cursor":    [fonts.GoogleFont("Google Sans"), fonts.Font("system-ui"), fonts.Font("Helvetica Neue"), fonts.Font("sans-serif")],
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
        self.custom_css = _build_css(p, _fkey)


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


_STEP_ICONS = {
    "pending": "radio_button_unchecked",
    "running": "sync",
    "done":    "check_circle",
    "error":   "error",
}

_PIPELINE_STEPS_DEFAULT = [
    ("Load video",                  "pending", ""),
    ("Object detection (YOLO)",     "pending", ""),
    ("Semantic analysis (VLM)",     "pending", ""),
    ("LLM summarization",           "pending", ""),
]


def _steps_html(steps: list) -> str:
    rows = []
    for name, state, detail in steps:
        icon = _STEP_ICONS.get(state, "radio_button_unchecked")
        detail_span = f'<span class="ps-detail">{detail}</span>' if detail else ""
        rows.append(
            f'<div class="pipeline-step {state}">'
            f'<span class="ps-icon material-symbols-outlined">{icon}</span>'
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
# Splash screen
# ---------------------------------------------------------------------------

def _splash_html(states: list | None = None, fading: bool = False) -> str:
    _icon_class = {
        "waiting": ("hourglass_empty", ""),
        "loading": ("sync",            "si-loading"),
        "ready":   ("check_circle",    "si-ready"),
        "error":   ("error",           "si-error"),
        "skipped": ("warning",         "si-skipped"),
    }
    _detail_text = {
        "waiting": "Waiting…",
        "loading": "Loading weights…",
        "ready":   "Ready",
        "error":   "Failed",
        "skipped": "Not available",
    }
    if states is None:
        from model_registry import get_states
        states = get_states()

    total = len(states)
    done_count = sum(1 for s in states if s.status in {"ready", "error", "skipped"})
    progress_pct = int(done_count / total * 100) if total else 0

    items_html = ""
    for s in states:
        icon, cls = _icon_class.get(s.status, ("hourglass_empty", ""))
        detail = s.detail if s.detail else _detail_text.get(s.status, "")
        items_html += (
            f'<div class="splash-item">'
            f'<span class="splash-item-icon material-symbols-outlined {cls}">{icon}</span>'
            f'<div class="splash-item-body">'
            f'<span class="splash-item-label">{s.label}</span>'
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
        f'<div class="splash-subtitle">AI Security Camera Agent</div>'
        f'<div class="splash-card">'
        f'<div class="splash-card-header">Initializing Models</div>'
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

        # ── Startup splash (ComfyUI-style model loading screen) ──────────────
        splash_html  = gr.HTML(value=_splash_html(), elem_id="splash-wrapper")
        splash_timer = gr.Timer(value=0.9, active=True)

        # ── Header ──────────────────────────────────────────────────────────
        with gr.Row():
            with gr.Column(scale=5, elem_id="eyas-header"):
                gr.HTML(_HEADER_HTML)
            with gr.Column(scale=1, min_width=160, elem_id="theme-col"):
                gr.HTML(f'<div class="eyas-theme-badge">Theme: <strong>{current_label}</strong></div>')

        event_log_state: gr.State = gr.State([])
        output_dir_state: gr.State = gr.State("")

        # ── Main layout: sidebar + analysis panel ────────────────────────────
        with gr.Row():

            # — Left sidebar: input ──────────────────────────────────────────
            with gr.Column(scale=1, min_width=260, elem_id="eyas-sidebar"):
                gr.HTML(
                    '<div class="eyas-panel-header">'
                    '<span class="ph-dot"></span>'
                    '<span class="ph-label">Footage</span>'
                    '</div>'
                )
                sample_dd = gr.Dropdown(
                    choices=list(_SAMPLE_PATHS.keys()),
                    label="Sample clips",
                    interactive=True,
                )
                load_sample_btn = gr.Button("Load Sample", variant="secondary", size="sm", elem_id="load-sample-btn")
                video_input = gr.Video(label="Original Video", sources=["upload"])
                upload_status = gr.Textbox(label="Storage", interactive=False, lines=1)

            # — Right panel: analysis + output ───────────────────────────────
            with gr.Column(scale=2, elem_id="eyas-main"):
                gr.HTML(
                    '<div class="eyas-panel-header">'
                    '<span class="ph-dot"></span>'
                    '<span class="ph-label">Analysis</span>'
                    '</div>'
                )
                analyze_btn = gr.Button(
                    "Analyze", variant="primary", size="lg", elem_id="analyze-btn",
                )
                status_box = gr.Textbox(
                    label="Status", interactive=False, lines=1,
                    elem_id="status-box",
                )
                pipeline_html = gr.HTML(_steps_html(_PIPELINE_STEPS_DEFAULT))
                annotated_img = gr.Image(label="Annotated (Live)", interactive=False)
                annotated_vid = gr.Video(label="Annotated Video", interactive=False, visible=False)

        video_input.change(fn=None, inputs=[video_input], js=_REC_JS)

        # ── Tabs ────────────────────────────────────────────────────────────
        with gr.Tabs(selected=0):

            with gr.TabItem("Event Timeline"):
                with gr.Row():
                    _section_title("Detected Events")
                    refresh_events_btn = gr.Button(
                        "", variant="secondary", size="sm",
                        elem_id="refresh-events-btn", scale=0, min_width=40,
                    )
                event_table = gr.DataFrame(
                    headers=["#", "Event", "Activity", "Start", "End", "Zone", "Confidence", "Clip"],
                    label="Event Log", interactive=False, wrap=True, elem_id="event-table",
                )
                with gr.Row():
                    with gr.Column(scale=2):
                        clip_selector = gr.Dropdown(label="Select clip to preview", choices=[], interactive=True)
                    with gr.Column(scale=3):
                        clip_preview = _clip_video("Clip Preview")

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
                        flagged_clip_preview = _clip_video("Flagged Clip Preview")

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
                    load_clip_btn   = gr.Button("Load for Analysis", variant="primary", size="sm", scale=1)
                    delete_clip_btn = gr.Button("Delete", variant="stop", size="sm", scale=1)

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

        # Shared live-event state — written by the pipeline thread, read by the refresh button
        _live_events: list = []
        _live_rows: list = []

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

        # ── Splash timer — polls model registry, fades splash when ready ──────
        def _poll_splash():
            done = _mreg.all_done()
            return _splash_html(fading=done), gr.update(active=not done)

        splash_timer.tick(_poll_splash, outputs=[splash_html, splash_timer])

        def run_pipeline(video_path):
            import tempfile
            import time as _time
            import cv2 as _cv2
            from visual_pipeline import run_visual_pipeline

            _preloaded_reasoner = _mreg.get("llm")
            def _summarize(events):
                if _preloaded_reasoner is not None:
                    return _preloaded_reasoner.summarize_events(events)
                from llm.reasoner import summarize_events as _fallback
                return _fallback(events)

            steps = list(_PIPELINE_STEPS_DEFAULT)  # mutable copy
            step_start: dict = {}
            _last_frame: list = [None]  # latest annotated frame (RGB numpy array)
            _live_events.clear()
            _live_rows.clear()

            def _blank():
                return ([], [], gr.update(choices=[]), "", {"none": 1.0},
                        [], gr.update(choices=[]), {}, 0, 0, 0, 0,
                        gr.update(visible=False), gr.update(visible=False), "")

            def emit(status):
                f = _last_frame[0]
                ann = gr.update(value=f, visible=f is not None) if f is not None else gr.update(visible=False)
                return (
                    _steps_html(_annotate_elapsed(steps, step_start)), status,
                    list(_live_events), list(_live_rows), gr.update(choices=[]), "", {"none": 1.0},
                    [], gr.update(choices=[]), {}, 0, 0, 0, 0,
                    ann,
                    gr.update(visible=False),
                    "",
                )

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
                    ev_kind = "pickup" if ev.get("pickup_confirmed") else "observation"
                    activity = (ev.get("activity") or "").strip() or "—"
                    clip_name = "—"
                    if ev.get("pickup_confirmed"):
                        picked = ev.get("picked_up_items") or []
                        if picked:
                            clip_name = picked[0].get("name", "—") or "—"
                    _live_events.append(ev)
                    _live_rows.append([
                        i, ev_kind, activity,
                        _fmt_time(ev.get("timestamp")),
                        _fmt_time(ev.get("confirmation_timestamp")) or "—",
                        ev.get("zone", "") or "—",
                        round(float(ev.get("confidence", 0)), 2),
                        clip_name,
                    ])
                    print(
                        f"[EVENT #{i}] {_fmt_time(ev.get('timestamp'))} | "
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
                    _, done, total, track_count, vlm_fired, display_frame = msg
                    if display_frame is not None:
                        _last_frame[0] = display_frame
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
                kind = "pickup" if ev.get("pickup_confirmed") else "observation"
                activity = (ev.get("activity") or "").strip() or "—"
                clip_name = "—"
                if ev.get("pickup_confirmed"):
                    picked_up_items = ev.get("picked_up_items") or []
                    if picked_up_items:
                        clip_name = picked_up_items[0].get("name", "—") or "—"
                rows.append([
                    i, kind,
                    activity,
                    _fmt_time(ev.get("timestamp")),
                    _fmt_time(ev.get("confirmation_timestamp")) or "—",
                    ev.get("zone", "") or "—",
                    round(float(ev.get("confidence", 0)), 2),
                    clip_name,
                ])
            zone_counts = {"entrance": 0, "counter": 0, "back_door": 0, "aisles": 0}
            for ev in events:
                z = ev.get("zone", "").lower().replace(" ", "_")
                if z in zone_counts:
                    zone_counts[z] += 1

            f = _last_frame[0]
            yield (
                _steps_html(_annotate_elapsed(steps, step_start)), "Running LLM summarization…",
                events, rows, gr.update(choices=[]),
                "", {"none": 1.0}, [], gr.update(choices=[]),
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
                llm = {"summary": "LLM unavailable — no model loaded.",
                       "flags": [], "suspicious_clips": [], "risk_level": "none"}

            _finish_step(3, "LLM summarization", f"risk: {llm['risk_level']}")
            status = (
                f"Done. {vp.frames_processed} frames · "
                f"{vp.unique_tracks} tracks · {len(events)} events."
            )
            ann_vid_path = vp.annotated_video_path
            yield (
                _steps_html(_annotate_elapsed(steps, step_start)), status,
                events, rows, gr.update(choices=[]),
                llm["summary"], {llm["risk_level"]: 1.0},
                llm["flags"], gr.update(choices=llm["suspicious_clips"]),
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
                summary_box, risk_badge, flags_box, suspicious_clips_dd,
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
            if not message.strip():
                return history, ""
            if not events:
                reply = "No events loaded yet — please upload and analyze a video first."
            else:
                try:
                    _r = _mreg.get("llm")
                    if _r is not None:
                        result = _r.answer_query(events, message)
                    else:
                        from llm.reasoner import answer_query as _answer
                        result = _answer(events, message)
                    reply = result["answer"]
                    if result.get("clips"):
                        reply += "\n\nRelated clips: " + ", ".join(result["clips"])
                except Exception as exc:
                    reply = f"LLM error: {exc}"
            history = list(history) + [
                {"role": "user",      "content": message},
                {"role": "assistant", "content": reply},
            ]
            return history, ""

        ask_btn.click(ask_footage, inputs=[query_input, chatbot, event_log_state], outputs=[chatbot, query_input])
        query_input.submit(ask_footage, inputs=[query_input, chatbot, event_log_state], outputs=[chatbot, query_input])
        clear_btn.click(lambda: ([], ""), outputs=[chatbot, query_input])

        def generate_audio(events: List[Dict]):
            if not events:
                return None
            try:
                _r = _mreg.get("llm")
                if _r is not None:
                    llm = _r.summarize_events(events)
                else:
                    from llm.reasoner import summarize_events as _summarize
                    llm = _summarize(events)
                text = llm.get("summary", "").strip()
                if not text:
                    return None
                import numpy as np
                preloaded_tts = _mreg.get("tts")
                if preloaded_tts is not None:
                    model, sample_rate = preloaded_tts
                    chunks = list(model.generate_streaming(text=f"(A young woman, gentle and sweet voice){text}"))
                    if not chunks:
                        return None
                    audio = np.concatenate([c.astype(np.float32) for c in chunks])
                else:
                    from postprocessing.translate_tts import tts
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
