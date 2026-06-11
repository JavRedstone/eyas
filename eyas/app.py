"""Launcher for the Eyas prototype.

Language is read from preferences.json at startup and can be overridden via CLI flags:

    python app.py                 # use preferences.json
    python app.py --lang ko       # Korean UI
"""

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from ui.gradio_app import build_app

_PREFS = Path(__file__).parent / "preferences.json"
_DEFAULTS = {"language": "en"}


def _load_prefs() -> dict:
    try:
        return {**_DEFAULTS, **json.loads(_PREFS.read_text())}
    except Exception:
        return dict(_DEFAULTS)


def _parse_args(prefs: dict) -> dict:
    parser = argparse.ArgumentParser(description="Eyas — AI Security Camera Agent")
    parser.add_argument(
        "--lang",
        choices=["en", "ko"],
        default=None,
        help="UI language (overrides preferences.json)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Gradio server port. Default: automatically choose from 7860-7959.",
    )
    args = parser.parse_args()

    result = dict(prefs)
    if args.lang is not None:
        result["language"] = args.lang
    if args.port is not None:
        result["port"] = args.port
    return result


prefs = _parse_args(_load_prefs())
app, _theme = build_app(
    language=prefs.get("language", "en"),
    prefs_path=_PREFS,
)

if __name__ == "__main__":
    app.launch(
        theme=_theme,
        css=_theme.custom_css,
        server_port=prefs.get("port"),
    )
