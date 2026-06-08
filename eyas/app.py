"""Launcher for the Eyas prototype.

Theme is read from preferences.json at startup and can be overridden
via CLI flags:

    python app.py                        # use preferences.json
    python app.py --theme amber          # Amber CRT (dark)
    python app.py --theme sentinel --light  # Sentinel light
    python app.py --advanced voltagent   # Advanced DESIGN.md theme
"""

import argparse
import json
from pathlib import Path

from ui.gradio_app import build_app

_PREFS = Path(__file__).parent / "preferences.json"
_DEFAULTS = {"theme": "night", "dark": True}


def _load_prefs() -> dict:
    try:
        return {**_DEFAULTS, **json.loads(_PREFS.read_text())}
    except Exception:
        return dict(_DEFAULTS)


def _parse_args(prefs: dict) -> dict:
    parser = argparse.ArgumentParser(description="Eyas — AI Security Camera Agent")
    parser.add_argument(
        "--theme",
        choices=["night", "amber", "cyber", "sentinel"],
        default=None,
        help="Simple colour theme (overrides preferences.json)",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dark",  dest="dark", action="store_true",  default=None, help="Dark mode")
    group.add_argument("--light", dest="dark", action="store_false",            help="Light mode")
    parser.add_argument(
        "--advanced",
        default=None,
        help="Advanced DESIGN.md theme key (overrides preferences.json)",
    )
    args = parser.parse_args()

    result = dict(prefs)
    if args.theme is not None:
        result["theme"] = args.theme
        result.pop("advanced", None)
    if args.dark is not None:
        result["dark"] = args.dark
    if args.advanced is not None:
        result["advanced"] = args.advanced
    return result


prefs = _parse_args(_load_prefs())
app   = build_app(
    color=prefs.get("theme", "night"),
    dark=prefs.get("dark", True),
    advanced=prefs.get("advanced"),
    prefs_path=_PREFS,
)

if __name__ == "__main__":
    app.launch()
