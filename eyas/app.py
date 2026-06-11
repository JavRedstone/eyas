"""Launcher for the Eyas prototype.

Language is read from preferences.json at startup and can be overridden via CLI flags:

    python app.py                 # use preferences.json
    python app.py --lang ko       # Korean UI
    gradio app.py                 # hot-reload dev mode
"""

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from ui.gradio_app import build_app

_PREFS = Path(__file__).parent / "preferences.json"
_DEFAULTS = {"language": "en"}
_STATIC_DIR = Path(__file__).parent / "ui" / "dist"


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
    # parse_known_args so gradio CLI args don't break module import
    args, _ = parser.parse_known_args()

    result = dict(prefs)
    if args.lang is not None:
        result["language"] = args.lang
    if args.port is not None:
        result["port"] = args.port
    return result


prefs = _parse_args(_load_prefs())
app = build_app(
    language=prefs.get("language", "en"),
    prefs_path=_PREFS,
)

_ALLOWED = [
    str(Path(__file__).parent / "input"),
    str(Path(__file__).parent / "data"),
]

app.launch(
    server_port=prefs.get("port"),
    allowed_paths=_ALLOWED,
    prevent_thread_lock=True,
)

# After launch(), demo.app is the live server — mount the React build and override GET /.
app.app.mount("/ui", StaticFiles(directory=str(_STATIC_DIR)), name="ui-static")

_INDEX_PATH = _STATIC_DIR / "index.html"


@app.app.get("/", response_class=HTMLResponse)
async def _root():
    # Read from disk each time so a React rebuild takes effect without restarting.
    return HTMLResponse(content=_INDEX_PATH.read_text())


# Gradio already registered its own GET / inside launch(); move ours to position 0.
_our_route = next(
    r for r in app.app.routes
    if getattr(r, "path", "") == "/" and getattr(r, "endpoint", None) is _root
)
app.app.routes.remove(_our_route)
app.app.routes.insert(0, _our_route)

# Block the main thread only when run directly; gradio CLI manages its own blocking.
if __name__ == "__main__":
    app.block_thread()
