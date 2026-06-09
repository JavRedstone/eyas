"""Shared pytest configuration and utilities for the eyas test suite."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from utils.device import get_device  # noqa: E402


@pytest.fixture(scope="session")
def device() -> str:
    return get_device()
