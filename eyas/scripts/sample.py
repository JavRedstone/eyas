"""Sample the reasoning pipeline against a structured event log.

Loads input/events.json (or a path you supply), runs the LLM reasoner,
and prints a formatted security report to stdout.

Usage:
    python scripts/sample.py                          # uses input/events.json
    python scripts/sample.py path/to/events.json      # custom event file
    python scripts/sample.py --query "Who picked up items?"
    python scripts/sample.py --no-summary --no-alert  # only Q&A

Environment:
    EYAS_MODEL_PATH   path to the GGUF model file (default: models/nemotron-nano-4b.gguf)
    EYAS_GPU_LAYERS   number of GPU layers to offload (default: -1 = all)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from pathlib import Path

# Allow running as `python scripts/sample.py` from anywhere inside the repo
_REPO_ROOT = Path(__file__).parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_EYAS_ROOT = Path(__file__).parent.parent
_DEFAULT_EVENTS = _EYAS_ROOT / "input" / "events.json"
_DEFAULT_MODEL  = Path(os.getenv("EYAS_MODEL_PATH", "models/nemotron-nano-4b.gguf"))

_DEFAULT_QUERIES = [
    "Anything suspicious happening in the store?",
    "Which tracks show confirmed pickups?",
    "Which zone had the most activity?",
]

_SEP  = "-" * 72
_SEP2 = "=" * 72


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _header(title: str) -> None:
    print(f"\n{_SEP2}")
    print(f"  {title}")
    print(_SEP2)


def _section(title: str) -> None:
    print(f"\n{_SEP}")
    print(f"  {title}")
    print(_SEP)


def _wrap(text: str, indent: int = 4) -> str:
    prefix = " " * indent
    return textwrap.fill(text, width=72, initial_indent=prefix, subsequent_indent=prefix)


def _print_summary(result: dict) -> None:
    _section("OVERNIGHT SUMMARY")
    print(_wrap(result.get("summary", "(no summary)")))

    risk = result.get("risk_level", "none").upper()
    risk_colour = {"NONE": "", "LOW": "", "MEDIUM": "⚠ ", "HIGH": "🔴 "}.get(risk, "")
    print(f"\n  Risk level : {risk_colour}{risk}")

    flags = result.get("flags", [])
    if flags:
        print(f"  Flags      : {', '.join(flags)}")
    else:
        print("  Flags      : (none)")

    clips = result.get("suspicious_clips", [])
    if clips:
        print(f"  Clips      : {', '.join(clips)}")


def _print_answer(query: str, result: dict, idx: int) -> None:
    _section(f"Q{idx}: {query}")
    print(_wrap(result.get("answer", "(no answer)")))
    indices = result.get("relevant_event_indices", [])
    clips   = result.get("clips", [])
    if indices:
        print(f"\n  Relevant events : {indices}")
    if clips:
        print(f"  Related clips   : {', '.join(clips)}")


def _print_alert(result: dict, event: dict) -> None:
    _section(f"ALERT — Track {event.get('track_id')} @ t={event.get('timestamp'):.2f}s")
    print(_wrap(result.get("alert", "(no alert)")))
    print(f"\n  Severity : {result.get('severity', '?').upper()}")
    if result.get("clip"):
        print(f"  Clip     : {result['clip']}")


def _print_events_table(events: list) -> None:
    _section(f"EVENT LOG  ({len(events)} events, "
             f"{len({e['track_id'] for e in events})} tracks)")
    header_fmt = "  {:>5}  {:>7}  {:>12}  {:>6}  {}"
    row_fmt    = "  {:>5}  {:>6.2f}s  {:>12}  {:>6}  {}"
    print(header_fmt.format("TRACK", "TIME", "ZONE", "CONF", "ACTIVITY"))
    print("  " + "-" * 68)
    for ev in events:
        pickup = " [PICKUP]" if ev.get("pickup_confirmed") else ""
        print(row_fmt.format(
            ev.get("track_id", "?"),
            ev.get("timestamp", 0.0),
            (ev.get("zone") or "-")[:12],
            f"{ev.get('confidence', 0):.3f}",
            (ev.get("activity") or "-")[:38] + pickup,
        ))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Eyas reasoning sampler")
    parser.add_argument("events_file", nargs="?", default=str(_DEFAULT_EVENTS),
                        help="Path to a structured events JSON file")
    parser.add_argument("--model", default=str(_DEFAULT_MODEL),
                        help="Path to the GGUF model file")
    parser.add_argument("--query", action="append", dest="queries",
                        help="Extra question(s) to ask (can repeat)")
    parser.add_argument("--no-summary", action="store_true", help="Skip the summary block")
    parser.add_argument("--no-qa",      action="store_true", help="Skip Q&A queries")
    parser.add_argument("--no-alert",   action="store_true", help="Skip the alert sample")
    parser.add_argument("--no-table",   action="store_true", help="Skip the event table")
    args = parser.parse_args()

    events_path = Path(args.events_file)
    if not events_path.exists():
        sys.exit(f"Error: event file not found: {events_path}")

    events: list = json.loads(events_path.read_text())
    if not events:
        sys.exit("Error: event file is empty.")

    model_path = Path(args.model)

    _header(f"Eyas Reasoning Sampler  |  {events_path.name}  ({len(events)} events)")

    if not args.no_table:
        _print_events_table(events)

    needs_model = not (args.no_summary and args.no_qa and args.no_alert)
    if needs_model and not model_path.exists():
        sys.exit(
            f"\nError: model file not found: {model_path}\n"
            f"Set EYAS_MODEL_PATH or pass --model to specify the GGUF file.\n"
            f"Use --no-summary --no-qa --no-alert to view the event table only."
        )

    from eyas.llm.reasoner import Reasoner
    r = Reasoner(str(model_path)) if needs_model else None

    if not args.no_summary and r:
        _section("Running summarize_events …")
        result = r.summarize_events(events)
        _print_summary(result)

    queries = list(_DEFAULT_QUERIES)
    if args.queries:
        queries = args.queries + queries

    if not args.no_qa and r:
        _section("Running answer_query …")
        for i, q in enumerate(queries, 1):
            result = r.answer_query(events, q)
            _print_answer(q, result, i)

    if not args.no_alert and r:
        pickup_events = [ev for ev in events if ev.get("pickup_confirmed")]
        if pickup_events:
            _section("Running generate_alert …")
            result = r.generate_alert(pickup_events[0])
            _print_alert(result, pickup_events[0])
        else:
            print("\n  (no confirmed pickups — skipping alert sample)")

    print(f"\n{_SEP2}\n  Done.\n{_SEP2}\n")


if __name__ == "__main__":
    main()
