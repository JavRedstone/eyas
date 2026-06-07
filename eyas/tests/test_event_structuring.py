"""Tests for eyas/event_structuring/structurer.py."""

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent
_EYAS_ROOT = Path(__file__).parent.parent
for _p in (_REPO_ROOT, _EYAS_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from eyas.event_structuring.structurer import build_events


class TestBuildEvents:
    def test_returns_list(self):
        assert isinstance(build_events([], []), list)

    def test_empty_inputs_returns_empty(self):
        assert build_events([], []) == []

    def test_non_empty_inputs_return_list(self):
        detections = [{"label": "person", "confidence": 0.9, "bbox": [0, 0, 100, 200]}]
        annotations = [{"action": "walking", "timestamp": "00:00:01"}]
        result = build_events(detections, annotations)
        assert isinstance(result, list)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
