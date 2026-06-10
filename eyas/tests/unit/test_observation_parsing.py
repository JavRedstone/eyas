"""Unit tests for video_processing.process — observation parsing and prompt sanity."""

import sys
import textwrap
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent.parent
_EYAS_ROOT = Path(__file__).parent.parent.parent
for _p in (_REPO_ROOT, _EYAS_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from video_processing.process import PERSON_STATUS_PROMPT, parse_person_observation  # noqa: E402

_W = 72


def _box(title: str, body: str) -> None:
    print(f"\n{'=' * _W}")
    print(f"  {title}")
    print(f"{'-' * _W}")
    for line in str(body).splitlines():
        print(
            textwrap.fill(line, width=_W - 4, initial_indent="  ", subsequent_indent="    ")
            if line.strip()
            else ""
        )
    print(f"{'=' * _W}")


class TestPersonStatusPrompt:
    def test_does_not_suggest_specific_products(self):
        _box("PERSON_STATUS_PROMPT (preview)", PERSON_STATUS_PROMPT[:300].strip())
        assert "red object" not in PERSON_STATUS_PROMPT
        assert "chocolate bar" not in PERSON_STATUS_PROMPT


class TestParsePersonObservation:
    def test_vague_activity_not_promoted_to_held_object(self):
        obs = parse_person_observation(
            '{"description":"a person","activity":"handling a small red object",'
            '"pickup_confirmed":false,"picked_up_items":[]}'
        )
        _box(
            "vague activity",
            f"held_objects={obs.held_objects}  pickup_confirmed={obs.pickup_confirmed}",
        )
        assert obs.held_objects == []
        assert obs.picked_up_items == []

    def test_explicit_held_object_retained_without_confirming_pickup(self):
        obs = parse_person_observation(
            '{"description":"a person","activity":"standing",'
            '"held_objects":[{"name":"bottle","count":1}],'
            '"pickup_confirmed":false,"picked_up_items":[]}'
        )
        assert obs.held_objects == [{"name": "bottle", "count": 1}]
        assert obs.picked_up_items == []

    def test_explicit_holding_phrase_populates_held_object(self):
        obs = parse_person_observation(
            '{"description":"a person holding a small red object",'
            '"activity":"walking","held_objects":[]}'
        )
        assert obs.held_objects == [{"name": "small red object", "count": 1}]

    def test_negated_holding_phrase_does_not_populate_held_object(self):
        obs = parse_person_observation(
            '{"description":"a person","activity":"initially not holding any objects; '
            'then moves near a shelf","held_objects":[]}'
        )
        assert obs.held_objects == []


if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
