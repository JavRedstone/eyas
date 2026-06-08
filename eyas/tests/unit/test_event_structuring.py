"""Unit tests for eyas/event_structuring/structurer.py."""

import sys
import textwrap
from pathlib import Path

import numpy as np
import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent.parent
_EYAS_ROOT = Path(__file__).parent.parent.parent
for _p in (_REPO_ROOT, _EYAS_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from eyas.event_structuring.structurer import build_events, EventStructurer, Zone  # noqa: E402
from eyas.object_detection.detector import Track  # noqa: E402
from eyas.video_processing.process import parse_person_observation  # noqa: E402

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


class TestEvidenceCrops:
    def test_crops_share_one_context_region(self):
        structurer = EventStructurer(
            [Zone("all", (0, 0, 200, 200))],
            vlm=object(),
            crop_pad=10,
            evidence_window_s=2,
            evidence_frames=3,
        )
        frame = np.zeros((200, 200, 3), dtype=np.uint8)
        structurer._remember(Track(1, "person", 0.9, (40, 50, 80, 150)), 0.0, frame)
        structurer._remember(Track(1, "person", 0.9, (60, 40, 100, 140)), 1.0, frame)
        structurer._remember(Track(1, "person", 0.9, (80, 30, 120, 130)), 2.0, frame)
        crops = structurer._evidence_crops(1)
        assert len(crops) == 3
        assert all(crop.shape == (140, 100, 3) for crop in crops)


class TestPickupInference:
    def _make_sequence_vlm(self, first_json: str, second_json: str):
        class _VLM:
            backend = "test"
            calls = 0

            def observe_person(self, frames, track_id=None):
                self.calls += 1
                return parse_person_observation(first_json if self.calls == 1 else second_json)

        return _VLM()

    def test_recent_interaction_then_new_held_object_confirms_pickup(self):
        vlm = self._make_sequence_vlm(
            '{"activity":"reaching toward items on a shelf","held_objects":[],"pickup_confirmed":false}',
            '{"description":"a person holding a small object","activity":"walking","held_objects":[],"pickup_confirmed":false}',
        )
        structurer = EventStructurer(
            [Zone("all", (0, 0, 200, 200))], vlm=vlm, semantic_interval_s=0
        )
        frame = np.zeros((200, 200, 3), dtype=np.uint8)
        track = Track(1, "person", 0.9, (40, 40, 120, 180))
        structurer.update([track], 0.0, frame)
        events = structurer.update([track], 1.0, frame)
        assert events[0].pickup_confirmed is False
        assert structurer.events[0].timestamp == 0.0
        assert structurer.events[0].confirmation_timestamp == 1.0
        assert structurer.events[0].pickup_confirmed is True
        assert structurer.events[0].picked_up_items == [{"name": "small object", "count": 1}]

    def test_tiny_track_cannot_infer_pickup(self):
        vlm = self._make_sequence_vlm(
            '{"activity":"reaching toward items","held_objects":[]}',
            '{"description":"a person holding an object","held_objects":[]}',
        )
        structurer = EventStructurer(
            [Zone("all", (0, 0, 1000, 1000))], vlm=vlm, semantic_interval_s=0
        )
        frame = np.zeros((1000, 1000, 3), dtype=np.uint8)
        tiny_track = Track(1, "person", 0.9, (0, 0, 100, 100))
        structurer.update([tiny_track], 0.0, frame)
        events = structurer.update([tiny_track], 1.0, frame)
        assert events[0].pickup_confirmed is False


if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
