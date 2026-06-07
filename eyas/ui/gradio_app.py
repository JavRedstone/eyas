"""Gradio UI for Eyas — Offline CCTV Security Assistant.

Custom dark-console theme targets the Off-Brand bonus quest.
"""

from typing import Dict, List

import gradio as gr

# ── Dark surveillance-console theme ──────────────────────────────────────────
_CSS = """
/* ── Root palette ──────────────────────────────────────────── */
:root {
    --bg:        #0a0e17;
    --panel:     #111827;
    --surface:   #1f2937;
    --border:    #2d3748;
    --accent:    #10b981;
    --accent-dk: #064e3b;
    --text:      #e5e7eb;
    --muted:     #6b7280;
    --danger:    #f87171;
    --mono:      'Courier New', Consolas, monospace;
}

/* ── Page background ────────────────────────────────────────── */
body, .gradio-container, .main, footer { background: var(--bg) !important; }
footer { display: none !important; }

/* ── Panels / blocks ────────────────────────────────────────── */
.block, .form, .gr-group {
    background: var(--panel) !important;
    border-color: var(--border) !important;
    border-radius: 6px !important;
}

/* ── Text inputs & textareas ────────────────────────────────── */
input[type="text"], input[type="number"],
textarea, select, .scroll-hide {
    background: var(--surface) !important;
    color: var(--text) !important;
    border-color: var(--border) !important;
    font-family: var(--mono) !important;
}
input:focus, textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(16,185,129,.2) !important;
    outline: none !important;
}

/* ── Labels ─────────────────────────────────────────────────── */
label span, .block > label > span {
    color: var(--muted) !important;
    font-size: 0.7rem !important;
    text-transform: uppercase !important;
    letter-spacing: .08em !important;
}

/* ── Buttons ─────────────────────────────────────────────────── */
button.primary {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
    color: #fff !important;
    font-weight: 600 !important;
    letter-spacing: .05em !important;
}
button.primary:hover  { background: #059669 !important; }
button.secondary {
    background: var(--surface) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
}
button.secondary:hover { border-color: var(--accent) !important; color: var(--accent) !important; }

/* ── Tabs ────────────────────────────────────────────────────── */
.tab-nav { border-bottom: 1px solid var(--border) !important; }
.tab-nav button {
    background: transparent !important;
    color: var(--muted) !important;
    border-bottom: 2px solid transparent !important;
    text-transform: uppercase !important;
    font-size: .75rem !important;
    letter-spacing: .07em !important;
    padding: 8px 16px !important;
}
.tab-nav button.selected {
    color: var(--accent) !important;
    border-bottom-color: var(--accent) !important;
    background: transparent !important;
}

/* ── DataFrame / event table ────────────────────────────────── */
table { background: var(--panel) !important; border-color: var(--border) !important; }
thead, thead tr { background: var(--surface) !important; }
th {
    color: var(--accent) !important;
    font-family: var(--mono) !important;
    font-size: .68rem !important;
    text-transform: uppercase !important;
    letter-spacing: .1em !important;
    padding: 8px 12px !important;
    border-color: var(--border) !important;
}
td {
    color: var(--text) !important;
    font-family: var(--mono) !important;
    font-size: .8rem !important;
    border-color: var(--border) !important;
    padding: 6px 12px !important;
}
tr:hover td { background: var(--surface) !important; }

/* ── JSON display ────────────────────────────────────────────── */
.json-holder, .json-holder * {
    background: var(--surface) !important;
    color: var(--text) !important;
    font-family: var(--mono) !important;
    font-size: .78rem !important;
}

/* ── Chatbot ─────────────────────────────────────────────────── */
.chatbot, .chatbot > div { background: var(--panel) !important; }
.message { color: var(--text) !important; font-size: .85rem !important; }
.message.user   .bubble-wrap { background: var(--accent-dk) !important; border-radius: 8px 8px 2px 8px !important; }
.message.bot    .bubble-wrap { background: var(--surface)   !important; border-radius: 8px 8px 8px 2px !important; }

/* ── Dropdowns ───────────────────────────────────────────────── */
.dropdown-arrow, .dropdown svg { color: var(--muted) !important; fill: var(--muted) !important; }
ul.options { background: var(--surface) !important; border-color: var(--border) !important; }
li.item { color: var(--text) !important; }
li.item:hover, li.item.selected { background: var(--accent-dk) !important; color: var(--accent) !important; }

/* ── Scrollbars ──────────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }

/* ── Header ──────────────────────────────────────────────────── */
#eyas-header { border-bottom: 1px solid var(--border); padding-bottom: 14px; margin-bottom: 4px; }
#eyas-header h1 {
    color: var(--accent) !important;
    font-family: var(--mono) !important;
    letter-spacing: .12em !important;
    font-size: 1.5rem !important;
}
#eyas-header p { color: var(--muted) !important; font-size: .82rem !important; margin-top: 4px !important; }

/* blinking REC dot */
#eyas-header h1::before {
    content: "● REC  ";
    color: var(--danger);
    font-size: .75em;
    animation: blink 1.4s step-start infinite;
}
@keyframes blink { 50% { opacity: 0; } }

/* ── Status textbox ──────────────────────────────────────────── */
#status-box textarea {
    font-family: var(--mono) !important;
    font-size: .78rem !important;
    color: var(--accent) !important;
}

/* ── Zone count numbers ──────────────────────────────────────── */
#count-entrance input, #count-counter input,
#count-back-door input, #count-aisles input {
    font-family: var(--mono) !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
    text-align: center !important;
    color: var(--accent) !important;
}

/* ── Markdown headings inside panels ─────────────────────────── */
.block h3 {
    color: var(--text) !important;
    font-size: .85rem !important;
    text-transform: uppercase !important;
    letter-spacing: .08em !important;
    border-bottom: 1px solid var(--border);
    padding-bottom: 6px;
    margin-bottom: 10px;
}
.block em { color: var(--muted) !important; }
"""


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Eyas — CCTV Security Assistant") as demo:

        # ── Header ───────────────────────────────────────────────────────────
        with gr.Column(elem_id="eyas-header"):
            gr.Markdown("# Eyas — CCTV Security Assistant")
            gr.Markdown(
                "Upload a video clip to generate a structured security event log, "
                "get an AI summary, and ask questions about what happened."
            )

        # ── Shared state ──────────────────────────────────────────────────
        event_log_state: gr.State = gr.State([])

        # ── Input row ─────────────────────────────────────────────────────
        with gr.Row():
            with gr.Column(scale=3):
                video_input = gr.Video(label="Upload CCTV clip (.mp4)", sources=["upload"])
            with gr.Column(scale=1):
                analyze_btn = gr.Button("Analyze", variant="primary", size="lg")
                status_box = gr.Textbox(
                    label="Status", interactive=False, lines=3, elem_id="status-box"
                )

        # ── Output tabs ───────────────────────────────────────────────────
        with gr.Tabs():

            # ── Tab 1 · Event Timeline ────────────────────────────────────
            with gr.TabItem("Event Timeline"):
                gr.Markdown("### Detected Events")
                event_table = gr.DataFrame(
                    headers=["#", "Type", "Start", "End", "Zone", "Confidence", "Clip"],
                    label="Event Log",
                    interactive=False,
                    wrap=True,
                )
                with gr.Row():
                    with gr.Column(scale=2):
                        clip_selector = gr.Dropdown(
                            label="Select clip to preview",
                            choices=[],
                            interactive=True,
                        )
                    with gr.Column(scale=3):
                        clip_player = gr.Video(label="Clip Preview", interactive=False)

            # ── Tab 2 · Summary & Alerts ──────────────────────────────────
            with gr.TabItem("Summary & Alerts"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### AI Security Summary")
                        summary_box = gr.Textbox(
                            label="Overnight Summary",
                            lines=6,
                            interactive=False,
                        )
                        risk_badge = gr.Label(label="Risk Level")
                    with gr.Column():
                        gr.Markdown("### Flagged Items")
                        flags_box = gr.JSON(label="Flags")
                        suspicious_clips_dd = gr.Dropdown(
                            label="Suspicious clips — select to preview",
                            choices=[],
                            interactive=True,
                        )
                        suspicious_clip_player = gr.Video(
                            label="Flagged Clip Preview", interactive=False
                        )

            # ── Tab 3 · Ask Footage ───────────────────────────────────────
            with gr.TabItem("Ask Footage"):
                gr.Markdown(
                    "### Ask a question about the footage\n"
                    "*e.g. 'Anything unusual overnight?', "
                    "'Show back door activity', "
                    "'What happened between 2–4 AM?'*"
                )
                chatbot = gr.Chatbot(label="Footage Q&A", height=420)
                with gr.Row():
                    query_input = gr.Textbox(
                        placeholder="Ask about the footage...",
                        label="Your question",
                        scale=5,
                        lines=1,
                    )
                    ask_btn = gr.Button("Ask", variant="primary", scale=1)
                clear_btn = gr.Button("Clear chat", variant="secondary", size="sm")

            # ── Tab 4 · Detection Metrics ─────────────────────────────────
            with gr.TabItem("Detection Metrics"):
                gr.Markdown("### Per-Zone Object Counts")
                with gr.Row():
                    count_entrance = gr.Number(
                        label="Entrance",  value=0, interactive=False, elem_id="count-entrance"
                    )
                    count_counter = gr.Number(
                        label="Counter",   value=0, interactive=False, elem_id="count-counter"
                    )
                    count_back_door = gr.Number(
                        label="Back Door", value=0, interactive=False, elem_id="count-back-door"
                    )
                    count_aisles = gr.Number(
                        label="Aisles",    value=0, interactive=False, elem_id="count-aisles"
                    )
                metrics_json = gr.JSON(label="Raw detection counts by zone")

            # ── Tab 5 · Audio Report ──────────────────────────────────────
            with gr.TabItem("Audio Report"):
                gr.Markdown("### Spoken Security Report")
                gr.Markdown(
                    "Generates a TTS audio playback of the AI summary "
                    "*(requires translation/TTS stage to be wired in)*."
                )
                audio_output = gr.Audio(label="TTS Report", interactive=False)
                generate_audio_btn = gr.Button(
                    "Generate Audio Report", variant="secondary"
                )

        # ── Callbacks ─────────────────────────────────────────────────────

        def run_pipeline(video_path: str | None):
            if video_path is None:
                return (
                    "No video uploaded.",
                    [],
                    [],
                    gr.Dropdown(choices=[]),
                    "",
                    {},
                    [],
                    gr.Dropdown(choices=[]),
                    {},
                    0, 0, 0, 0,
                )

            # TODO: replace stubs with real pipeline calls:
            # from eyas.scripts.split_clips import split_clips
            # from eyas.object_detection.detector import detect
            # from eyas.video_processing.process import process_clips
            # from eyas.event_structuring.structurer import build_events
            # from eyas.llm.reasoner import summarize_events
            #
            # clips       = split_clips(video_path)
            # detections  = detect(clips)
            # annotations = process_clips(clips)
            # events      = build_events(detections, annotations)
            # result      = summarize_events(events)

            events: List[Dict] = []
            result = {
                "summary": "(prototype) pipeline not yet connected.",
                "flags": [],
                "suspicious_clips": [],
                "risk_level": "none",
            }

            rows = [
                [
                    i,
                    ev.get("type"),
                    ev.get("start_time"),
                    ev.get("end_time"),
                    ev.get("zone"),
                    round(ev.get("metadata", {}).get("confidence", 0), 2),
                    ev.get("metadata", {}).get("clip_pointer", ""),
                ]
                for i, ev in enumerate(events)
            ]
            clips = list(
                {ev.get("metadata", {}).get("clip_pointer", "") for ev in events} - {""}
            )
            zone_counts = {"entrance": 0, "counter": 0, "back_door": 0, "aisles": 0}

            return (
                f"Done. {len(events)} event(s) detected.",
                events,
                rows,
                gr.Dropdown(choices=clips),
                result["summary"],
                {result["risk_level"]: 1.0},
                result["flags"],
                gr.Dropdown(choices=result["suspicious_clips"]),
                zone_counts,
                zone_counts["entrance"],
                zone_counts["counter"],
                zone_counts["back_door"],
                zone_counts["aisles"],
            )

        analyze_btn.click(
            run_pipeline,
            inputs=[video_input],
            outputs=[
                status_box,
                event_log_state,
                event_table,
                clip_selector,
                summary_box,
                risk_badge,
                flags_box,
                suspicious_clips_dd,
                metrics_json,
                count_entrance,
                count_counter,
                count_back_door,
                count_aisles,
            ],
        )

        def ask_footage(message: str, history: list, events: List[Dict]):
            if not message.strip():
                return history, ""

            if not events:
                reply = "No events loaded yet — please upload and analyze a video first."
            else:
                # TODO: uncomment once LLM reasoner is wired:
                # from eyas.llm.reasoner import answer_query
                # result = answer_query(events, message)
                result = {
                    "answer": "(prototype) LLM not yet connected.",
                    "relevant_event_indices": [],
                    "clips": [],
                }
                reply = result["answer"]
                if result["clips"]:
                    reply += f"\n\nRelated clips: {', '.join(result['clips'])}"

            history = history + [(message, reply)]
            return history, ""

        ask_btn.click(
            ask_footage,
            inputs=[query_input, chatbot, event_log_state],
            outputs=[chatbot, query_input],
        )
        query_input.submit(
            ask_footage,
            inputs=[query_input, chatbot, event_log_state],
            outputs=[chatbot, query_input],
        )
        clear_btn.click(lambda: ([], ""), outputs=[chatbot, query_input])

        def generate_audio(events: List[Dict]):
            if not events:
                return None
            # TODO: from eyas.postprocessing.translate_tts import translate_and_speak
            # return translate_and_speak(summary_text)
            return None

        generate_audio_btn.click(
            generate_audio,
            inputs=[event_log_state],
            outputs=[audio_output],
        )

    return demo
