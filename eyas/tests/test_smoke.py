import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_EYAS_ROOT = Path(__file__).parent.parent
for _p in (_REPO_ROOT, _EYAS_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import pytest

from video_processing.process import PERSON_STATUS_PROMPT, parse_person_observation
from event_structuring.structurer import EventStructurer, Zone
from object_detection.detector import Track

import numpy as np


def test_smoke():
    assert True


def test_status_prompt_does_not_suggest_specific_products():
    assert "red object" not in PERSON_STATUS_PROMPT
    assert "chocolate bar" not in PERSON_STATUS_PROMPT


def test_vague_activity_is_not_promoted_to_held_object():
    observation = parse_person_observation(
        '{"description":"a person","activity":"handling a small red object",'
        '"pickup_confirmed":false,"picked_up_items":[]}'
    )

    assert observation.held_objects == []
    assert observation.picked_up_items == []


def test_explicit_held_object_is_retained_without_confirming_pickup():
    observation = parse_person_observation(
        '{"description":"a person","activity":"standing",'
        '"held_objects":[{"name":"bottle","count":1}],'
        '"pickup_confirmed":false,"picked_up_items":[]}'
    )

    assert observation.held_objects == [{"name": "bottle", "count": 1}]
    assert observation.picked_up_items == []


def test_explicit_holding_phrase_populates_held_object():
    observation = parse_person_observation(
        '{"description":"a person holding a small red object",'
        '"activity":"walking","held_objects":[]}'
    )

    assert observation.held_objects == [{"name": "small red object", "count": 1}]


def test_evidence_crops_share_one_context_region():
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


def test_recent_interaction_then_new_held_object_confirms_pickup():
    class SequenceVLM:
        backend = "test"

        def __init__(self):
            self.calls = 0

        def observe_person(self, frames, track_id=None):
            self.calls += 1
            if self.calls == 1:
                return parse_person_observation(
                    '{"activity":"reaching toward items on a shelf",'
                    '"held_objects":[],"pickup_confirmed":false}'
                )
            return parse_person_observation(
                '{"description":"a person holding a small object",'
                '"activity":"walking","held_objects":[],"pickup_confirmed":false}'
            )

    structurer = EventStructurer(
        [Zone("all", (0, 0, 200, 200))],
        vlm=SequenceVLM(),
        semantic_interval_s=0,
    )
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    track = Track(1, "person", 0.9, (40, 40, 120, 180))
    structurer.update([track], 0.0, frame)
    events = structurer.update([track], 1.0, frame)

    assert events[0].pickup_confirmed is True
    assert events[0].picked_up_items == [{"name": "small object", "count": 1}]


def test_tiny_track_cannot_infer_pickup():
    class SequenceVLM:
        backend = "test"

        def __init__(self):
            self.calls = 0

        def observe_person(self, frames, track_id=None):
            self.calls += 1
            text = (
                '{"activity":"reaching toward items","held_objects":[]}'
                if self.calls == 1
                else '{"description":"a person holding an object","held_objects":[]}'
            )
            return parse_person_observation(text)

    structurer = EventStructurer(
        [Zone("all", (0, 0, 1000, 1000))],
        vlm=SequenceVLM(),
        semantic_interval_s=0,
    )
    frame = np.zeros((1000, 1000, 3), dtype=np.uint8)
    tiny_track = Track(1, "person", 0.9, (0, 0, 100, 100))
    structurer.update([tiny_track], 0.0, frame)
    events = structurer.update([tiny_track], 1.0, frame)

    assert events[0].pickup_confirmed is False


if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
