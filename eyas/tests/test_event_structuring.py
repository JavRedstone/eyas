"""Tests for eyas/event_structuring/structurer.py."""

import sys
import textwrap
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent
_EYAS_ROOT = Path(__file__).parent.parent
for _p in (_REPO_ROOT, _EYAS_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from eyas.event_structuring.structurer import build_events

_W = 72


def _box(title: str, body: str) -> None:
    print(f"\n{'=' * _W}")
    print(f"  {title}")
    print(f"{'-' * _W}")
    for line in str(body).splitlines():
        print(textwrap.fill(line, width=_W - 4, initial_indent="  ", subsequent_indent="    ") if line.strip() else "")
    print(f"{'=' * _W}")


class TestBuildEvents:
    def test_returns_list(self):
        assert isinstance(build_events([], []), list)

    def test_empty_inputs_returns_empty(self):
        assert build_events([], []) == []

    def test_non_empty_inputs_return_list(self):
        detections = [{"label": "person", "confidence": 0.9, "bbox": [0, 0, 100, 200]}]
        annotations = [{"action": "walking", "timestamp": "00:00:01"}]
        result = build_events(detections, annotations)
        _box(f"build_events result ({len(result)} events)", str(result) if result else "(empty)")
        assert isinstance(result, list)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
