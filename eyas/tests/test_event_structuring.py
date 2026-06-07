"""Tests for eyas/event_structuring/structurer.py."""

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
