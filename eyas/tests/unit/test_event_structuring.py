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
    def _make_vlm(self, observation_json: str):
        class _VLM:
            backend = "test"

            def observe_person(self, frames, track_id=None):
                return parse_person_observation(observation_json)

        return _VLM()

    def test_confirmed_pickup_with_held_object_is_recorded(self):
        vlm = self._make_vlm(
            '{"description":"a person holding a small object",'
            '"activity":"picking up a small object",'
            '"held_objects":[{"name":"small object","count":1}],'
            '"pickup_confirmed":true}'
        )
        structurer = EventStructurer(
            [Zone("all", (0, 0, 200, 200))], vlm=vlm, semantic_interval_s=0
        )
        frame = np.zeros((200, 200, 3), dtype=np.uint8)
        track = Track(1, "person", 0.9, (40, 40, 120, 180))
        events = structurer.update([track], 1.0, frame)
        assert events[0].timestamp == 1.0
        assert events[0].confirmation_timestamp == 1.0
        assert events[0].pickup_confirmed is True
        assert events[0].picked_up_items == [{"name": "small object", "count": 1}]

    def test_pickup_wording_without_object_is_recorded_without_inventing_item(self):
        vlm = self._make_vlm(
            '{"activity":"possibly picking something up",'
            '"held_objects":[],"pickup_confirmed":false}'
        )
        structurer = EventStructurer(
            [Zone("all", (0, 0, 200, 200))], vlm=vlm, semantic_interval_s=0
        )
        frame = np.zeros((200, 200, 3), dtype=np.uint8)
        events = structurer.update(
            [Track(1, "person", 0.9, (40, 40, 120, 180))], 1.0, frame
        )
        assert events[0].pickup_confirmed is True
        assert events[0].picked_up_items == []

    def test_confirmed_pickup_without_named_object_uses_generic_item(self):
        vlm = self._make_vlm(
            '{"activity":"the person reaches toward a shelf and picks up an item",'
            '"held_objects":[],"pickup_confirmed":true,"picked_up_items":[]}'
        )
        structurer = EventStructurer(
            [Zone("all", (0, 0, 200, 200))], vlm=vlm, semantic_interval_s=0
        )
        frame = np.zeros((200, 200, 3), dtype=np.uint8)
        events = structurer.update(
            [Track(1, "person", 0.9, (40, 40, 120, 180))], 1.0, frame
        )
        assert events[0].picked_up_items == [{"name": "retail item", "count": 1}]

    def test_hand_to_hold_transition_without_named_object_is_recorded(self):
        vlm = self._make_vlm(
            '{"activity":"the hand moves toward an item and then holds it",'
            '"held_objects":[],"pickup_confirmed":false,"picked_up_items":[]}'
        )
        structurer = EventStructurer(
            [Zone("all", (0, 0, 200, 200))], vlm=vlm, semantic_interval_s=0
        )
        frame = np.zeros((200, 200, 3), dtype=np.uint8)
        events = structurer.update(
            [Track(1, "person", 0.9, (40, 40, 120, 180))], 1.0, frame
        )
        assert events[0].pickup_confirmed is True
        assert events[0].picked_up_items == [{"name": "retail item", "count": 1}]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
