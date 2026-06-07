"""Tests for eyas/object_detection/detector.py."""

import sys
import textwrap
from pathlib import Path

import numpy as np
import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from eyas.object_detection.detector import Track, crop

ultralytics = pytest.importorskip.__module__  # just to note the pattern below

_W = 72


def _box(title: str, body: str) -> None:
    print(f"\n{'=' * _W}")
    print(f"  {title}")
    print(f"{'-' * _W}")
    for line in str(body).splitlines():
        print(textwrap.fill(line, width=_W - 4, initial_indent="  ", subsequent_indent="    ") if line.strip() else "")
    print(f"{'=' * _W}")


class TestTrack:
    def test_as_dict_contains_required_keys(self):
        t = Track(track_id=1, label="person", confidence=0.9, bbox=(10, 20, 100, 200))
        d = t.as_dict()
        _box("Track.as_dict()", str(d))
        assert {"track_id", "label", "confidence", "bbox"} <= d.keys()

    def test_bbox_serialised_as_list(self):
        t = Track(track_id=1, label="person", confidence=0.9, bbox=(10, 20, 100, 200))
        assert isinstance(t.as_dict()["bbox"], list)

    def test_confidence_preserved(self):
        t = Track(track_id=5, label="person", confidence=0.75, bbox=(0, 0, 50, 50))
        assert t.as_dict()["confidence"] == 0.75


class TestCrop:
    def test_returns_correct_region(self):
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        frame[10:50, 20:60] = 255
        out = crop(frame, (20, 10, 60, 50))
        assert out.shape == (40, 40, 3)

    def test_pad_clamps_to_frame(self):
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        out = crop(frame, (0, 0, 50, 50), pad=20)
        assert out.shape[0] <= 100
        assert out.shape[1] <= 100

    def test_zero_size_returns_empty(self):
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        out = crop(frame, (50, 50, 50, 50))
        assert out.size == 0


@pytest.mark.skipif(
    __import__("importlib").util.find_spec("ultralytics") is None,
    reason="ultralytics not installed",
)
class TestDetectObjects:
    def test_returns_list(self):
        from eyas.object_detection.detector import detect_objects
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        assert isinstance(detect_objects(frame), list)

    def test_detections_have_expected_keys_when_non_empty(self):
        from eyas.object_detection.detector import detect_objects
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        for det in detect_objects(frame):
            assert {"label", "confidence", "bbox"} <= det.keys()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
