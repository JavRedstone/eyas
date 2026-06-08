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


def test_interaction_trigger_skips_static_person():
    class CountingVLM:
        backend = "test"

        def __init__(self):
            self.calls = 0

        def observe_person(self, frames, track_id=None):
            self.calls += 1
            return parse_person_observation('{"activity":"standing"}')

    vlm = CountingVLM()
    structurer = EventStructurer(
        [Zone("all", (0, 0, 200, 200))],
        vlm=vlm,
        interaction_trigger=True,
        motion_threshold=0.01,
        evidence_window_s=1,
        evidence_frames=3,
    )
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    track = Track(1, "person", 0.9, (40, 40, 120, 180))
    for t in (0.0, 0.5, 1.0, 1.5):
        structurer.update([track], t, frame)

    assert vlm.calls == 0
    assert structurer.events == []


def test_interaction_trigger_waits_for_after_frame_then_observes_once():
    class CountingVLM:
        backend = "test"

        def __init__(self):
            self.calls = 0
            self.frame_counts = []

        def observe_person(self, frames, track_id=None):
            self.calls += 1
            self.frame_counts.append(len(frames))
            return parse_person_observation('{"activity":"reaching toward a shelf"}')

    vlm = CountingVLM()
    structurer = EventStructurer(
        [Zone("all", (0, 0, 200, 200))],
        vlm=vlm,
        interaction_trigger=True,
        motion_threshold=0.01,
        post_trigger_s=0.5,
        semantic_interval_s=2,
        evidence_window_s=1,
        evidence_frames=3,
    )
    track = Track(1, "person", 0.9, (40, 40, 120, 180))
    still = np.zeros((200, 200, 3), dtype=np.uint8)
    changed = still.copy()
    changed[60:130, 50:110] = 255

    structurer.update([track], 0.0, still)
    structurer.update([track], 0.5, changed)
    assert vlm.calls == 0
    structurer.update([track], 1.0, changed)

    assert vlm.calls == 1
    assert vlm.frame_counts == [3]
    assert len(structurer.events) == 1


def test_activity_picking_up_immediately_records_pickup():
    class PickupVLM:
        backend = "test"

        def observe_person(self, frames, track_id=None):
            return parse_person_observation(
                '{"description":"a person",'
                '"activity":"picking up a bottle",'
                '"held_objects":[{"name":"bottle","count":1}],'
                '"pickup_confirmed":false}'
            )

    structurer = EventStructurer(
        [Zone("all", (0, 0, 200, 200))],
        vlm=PickupVLM(),
        semantic_interval_s=0,
    )
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    events = structurer.update(
        [Track(1, "person", 0.9, (40, 40, 120, 180))],
        0.0,
        frame,
    )

    assert events[0].pickup_confirmed is True
    assert events[0].picked_up_items == [{"name": "bottle", "count": 1}]
    assert structurer.statuses[1].confirmed_pickups == [{"name": "bottle", "count": 1}]


def test_activity_picking_up_unknown_item_records_generic_item():
    class PickupVLM:
        backend = "test"

        def observe_person(self, frames, track_id=None):
            return parse_person_observation(
                '{"activity":"appears to be picking up something",'
                '"held_objects":[],"pickup_confirmed":false}'
            )

    structurer = EventStructurer(
        [Zone("all", (0, 0, 200, 200))],
        vlm=PickupVLM(),
        semantic_interval_s=0,
    )
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    events = structurer.update(
        [Track(1, "person", 0.9, (40, 40, 120, 180))], 0.0, frame
    )

    assert events[0].pickup_confirmed is True
    assert events[0].picked_up_items == [{"name": "retail item", "count": 1}]


def test_activity_picking_it_up_records_pickup():
    class PickupVLM:
        backend = "test"

        def observe_person(self, frames, track_id=None):
            return parse_person_observation(
                '{"activity":"interacts with an item, possibly picking it up or examining it"}'
            )

    structurer = EventStructurer(
        [Zone("all", (0, 0, 200, 200))],
        vlm=PickupVLM(),
        semantic_interval_s=0,
    )
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    events = structurer.update(
        [Track(1, "person", 0.9, (40, 40, 120, 180))], 0.0, frame
    )

    assert events[0].pickup_confirmed is True


def test_plain_interacting_with_items_does_not_confirm_pickup():
    class InteractionVLM:
        backend = "test"

        def observe_person(self, frames, track_id=None):
            return parse_person_observation(
                '{"activity":"bending over and interacting with retail items on a shelf"}'
            )

    structurer = EventStructurer(
        [Zone("all", (0, 0, 200, 200))],
        vlm=InteractionVLM(),
        semantic_interval_s=0,
    )
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    events = structurer.update(
        [Track(1, "person", 0.9, (40, 40, 120, 180))], 0.0, frame
    )

    assert events[0].pickup_confirmed is False


def test_negated_pickup_activity_does_not_confirm_pickup():
    class NoPickupVLM:
        backend = "test"

        def observe_person(self, frames, track_id=None):
            return parse_person_observation(
                '{"activity":"standing and observing shelves, '
                'no clear hand contact or movement to pick up objects",'
                '"pickup_confirmed":false}'
            )

    structurer = EventStructurer(
        [Zone("all", (0, 0, 200, 200))],
        vlm=NoPickupVLM(),
        semantic_interval_s=0,
    )
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    events = structurer.update(
        [Track(1, "person", 0.9, (40, 40, 120, 180))], 0.0, frame
    )

    assert events[0].pickup_confirmed is False
    assert events[0].picked_up_items == []


def test_negated_clause_does_not_hide_later_pickup_clause():
    class PickupVLM:
        backend = "test"

        def observe_person(self, frames, track_id=None):
            return parse_person_observation(
                '{"activity":"At first there is no movement to pick up an item. '
                'The person then picks it up.",'
                '"pickup_confirmed":false}'
            )

    structurer = EventStructurer(
        [Zone("all", (0, 0, 200, 200))],
        vlm=PickupVLM(),
        semantic_interval_s=0,
    )
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    events = structurer.update(
        [Track(1, "person", 0.9, (40, 40, 120, 180))], 0.0, frame
    )

    assert events[0].pickup_confirmed is True


def test_non_pickup_observation_is_recorded_as_event():
    class WalkingVLM:
        backend = "test"

        def observe_person(self, frames, track_id=None):
            return parse_person_observation(
                '{"description":"a person in a dark jacket","activity":"walking"}'
            )

    structurer = EventStructurer(
        [Zone("all", (0, 0, 200, 200))],
        vlm=WalkingVLM(),
        semantic_interval_s=0,
    )
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    events = structurer.update(
        [Track(1, "person", 0.9, (40, 40, 120, 180))], 0.0, frame
    )

    assert len(events) == 1
    assert events[0].pickup_confirmed is False
    assert events[0].description == "a person in a dark jacket"
    assert structurer.statuses[1].description == "a person in a dark jacket"


def test_returning_track_with_new_yolo_id_remains_distinct():
    class ReIdVLM:
        backend = "test"

        def observe_person(self, frames, track_id=None):
            return parse_person_observation(
                '{"description":"a person in a dark jacket and pants holding a yellow package",'
                '"activity":"walking"}'
            )

    structurer = EventStructurer(
        [Zone("all", (0, 0, 200, 200))],
        vlm=ReIdVLM(),
        semantic_interval_s=0,
    )
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    structurer.update([Track(2, "person", 0.9, (20, 20, 100, 180))], 0.0, frame)
    events = structurer.update([Track(7, "person", 0.9, (30, 20, 110, 180))], 3.0, frame)

    assert events[0].track_id == 7
    assert sorted(structurer.statuses) == [2, 7]
    assert structurer.display_statuses()[7].track_id == 7


def test_simultaneous_similar_tracks_remain_distinct():
    class ReIdVLM:
        backend = "test"

        def observe_person(self, frames, track_id=None):
            return parse_person_observation(
                '{"description":"a person in a dark jacket and pants","activity":"walking"}'
            )

    structurer = EventStructurer(
        [Zone("all", (0, 0, 200, 200))],
        vlm=ReIdVLM(),
        semantic_interval_s=0,
    )
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    structurer.update(
        [
            Track(2, "person", 0.9, (20, 20, 80, 180)),
            Track(7, "person", 0.9, (100, 20, 170, 180)),
        ],
        0.0,
        frame,
    )

    assert sorted(structurer.statuses) == [2, 7]
