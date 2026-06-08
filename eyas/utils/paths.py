"""Canonical path helpers for the eyas package."""

from __future__ import annotations

from pathlib import Path

_EYAS_ROOT = Path(__file__).parent.parent


def models_dir() -> Path:
    """Absolute path to the eyas/models/ directory."""
    return _EYAS_ROOT / "models"
