"""Launcher for the Eyas prototype.

Theme is read from preferences.json at startup and can be overridden
via CLI flags:

    python app.py                        # use preferences.json
    python app.py --theme amber          # Amber CRT (dark)
    python app.py --theme sentinel --light  # Sentinel light
"""

import argparse
import json
from pathlib import Path

from ui.gradio_app import EyasTheme, build_app

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
        help="Colour theme (overrides preferences.json)",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dark",  dest="dark", action="store_true",  default=None, help="Dark mode")
    group.add_argument("--light", dest="dark", action="store_false",            help="Light mode")
    args = parser.parse_args()

    result = dict(prefs)
    if args.theme is not None:
        result["theme"] = args.theme
    if args.dark is not None:
        result["dark"] = args.dark
    return result


prefs = _parse_args(_load_prefs())
theme = EyasTheme(color=prefs["theme"], dark=prefs["dark"])
app   = build_app(color=prefs["theme"], dark=prefs["dark"], prefs_path=_PREFS)

if __name__ == "__main__":
    app.launch(theme=theme)
