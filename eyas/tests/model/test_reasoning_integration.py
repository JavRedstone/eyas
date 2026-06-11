"""Integration test: run the LLM reasoner against tests/samples/events.json.

Format / adapter tests always run (no model needed) and print the
formatted event log so you can see exactly what the LLM receives.

Inference tests are skipped when the GGUF model file is absent;
when the model is present they print every LLM response.

Run and see all output:
    pytest tests/test_reasoning_integration.py -v -s

Or run directly:
    python tests/test_reasoning_integration.py -v -s

Set model path:
    EYAS_MODEL_PATH=models/mymodel.gguf pytest tests/test_reasoning_integration.py -v -s
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
from pathlib import Path

# Allow `python tests/test_reasoning_integration.py` without conftest.py
_REPO_ROOT = Path(__file__).parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import pytest

from eyas.llm.reasoner import Reasoner

_INPUT = Path(__file__).parent.parent / "samples" / "events.json"
_MODEL = Path(os.getenv("EYAS_MODEL_PATH", "models/nemotron-nano-4b.gguf"))
_model_available = _MODEL.exists()

_W = 72  # print width


def _box(title: str, body: str) -> None:
    print(f"\n{'=' * _W}")
    print(f"  {title}")
    print(f"{'-' * _W}")
    for line in body.splitlines():
        print(textwrap.fill(line, width=_W - 4, initial_indent="  ", subsequent_indent="    ") if line.strip() else "")
    print(f"{'=' * _W}")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def events() -> list:
    return json.loads(_INPUT.read_text())


@pytest.fixture(scope="module")
def reasoner() -> Reasoner:
    return Reasoner(str(_MODEL))


# ---------------------------------------------------------------------------
# Schema validation (always runs)
# ---------------------------------------------------------------------------

class TestEventsJson:
    def test_file_exists(self):
        assert _INPUT.exists(), f"tests/samples/events.json not found at {_INPUT}"

    def test_is_nonempty_list(self, events):
        assert isinstance(events, list) and len(events) > 0

    def test_required_fields_present(self, events):
        required = {"track_id", "timestamp", "zone", "activity", "confidence"}
        for ev in events:
            missing = required - ev.keys()
            assert not missing, f"Event missing fields: {missing}"

    def test_pickup_fields_are_lists(self, events):
        for ev in events:
            assert isinstance(ev.get("held_objects", []), list)
            assert isinstance(ev.get("picked_up_items", []), list)

    def test_timestamps_numeric_and_confidences_in_range(self, events):
        for ev in events:
            assert isinstance(ev["timestamp"], (int, float))
            assert 0.0 <= ev["confidence"] <= 1.0


# ---------------------------------------------------------------------------
# Format / adapter layer (always runs, prints formatted log)
# ---------------------------------------------------------------------------

class TestEventFormatting:
    def test_detects_observation_schema(self, events):
        assert all(Reasoner._is_observation_schema(ev) for ev in events)

    def test_formatted_log(self, events):
        """Print the formatted event log — this is what the LLM sees."""
        r = Reasoner("dummy.gguf")
        formatted = r._format_events(events)
        assert formatted.strip()
        _box(
            f"Formatted event log  ({len(events)} events -> {len(formatted)} chars)",
            formatted,
        )

    def test_format_includes_all_track_ids(self, events):
        r = Reasoner("dummy.gguf")
        formatted = r._format_events(events)
        for ev in events:
            assert f"Track {ev['track_id']}" in formatted

    def test_format_includes_zones_and_activities(self, events):
        r = Reasoner("dummy.gguf")
        formatted = r._format_events(events)
        for ev in events:
            if ev["zone"]:
                assert ev["zone"] in formatted
            if ev["activity"]:
                assert ev["activity"] in formatted

    def test_format_marks_confirmed_pickups(self, events):
        r = Reasoner("dummy.gguf")
        formatted = r._format_events(events)
        if any(ev.get("pickup_confirmed") for ev in events):
            assert "Pickup: YES" in formatted

    def test_trim_preserves_most_recent(self, events):
        r = Reasoner("dummy.gguf")
        trimmed = r._trim_events(events, max_chars=500)
        assert len(trimmed) >= 1
        assert trimmed[-1] == events[-1]

    def test_empty_events_fallback_no_model(self):
        r = Reasoner("dummy.gguf")
        result = r.summarize_events([])
        assert result["risk_level"] == "none"
        assert "No events" in result["summary"]


# ---------------------------------------------------------------------------
# Inference tests — skipped unless the model file is present
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not _model_available,
    reason=f"GGUF model not found at '{_MODEL}'. Set EYAS_MODEL_PATH to enable.",
)
class TestReasoningInference:

    def test_summarize(self, reasoner, events):
        result = reasoner.summarize_events(events)
        _box(
            "summarize_events",
            f"Summary    : {result.get('summary', '')}\n"
            f"Risk level : {result.get('risk_level', '').upper()}\n"
            f"Flags      : {', '.join(result.get('flags', [])) or '(none)'}\n"
            f"Clips      : {', '.join(result.get('suspicious_clips', [])) or '(none)'}",
        )
        assert isinstance(result, dict)
        assert {"summary", "flags", "suspicious_clips", "risk_level"} <= result.keys()
        assert result["risk_level"] in {"none", "low", "medium", "high"}
        assert result["summary"].strip()

    @pytest.mark.parametrize("query", [
        "Anything suspicious happening in the store?",
        "Which tracks show confirmed pickups?",
        "What was track 1 doing?",
        "Were any items picked up?",
        "Which zone had the most activity?",
    ])
    def test_answer_query(self, reasoner, events, query):
        result = reasoner.answer_query(events, query)
        _box(
            f"answer_query | {query}",
            f"Answer  : {result.get('answer', '')}\n"
            f"Events  : {result.get('relevant_event_indices', [])}\n"
            f"Clips   : {result.get('clips', [])}",
        )
        assert result["answer"].strip()

    def test_generate_alert(self, reasoner, events):
        pickup_events = [ev for ev in events if ev.get("pickup_confirmed")]
        if not pickup_events:
            pytest.skip("No confirmed pickups in input data")
        ev = pickup_events[0]
        result = reasoner.generate_alert(ev)
        _box(
            f"generate_alert | Track {ev['track_id']} @ t={ev['timestamp']:.2f}s",
            f"Alert    : {result.get('alert', '')}\n"
            f"Severity : {result.get('severity', '').upper()}\n"
            f"Clip     : {result.get('clip', '(none)')}",
        )
        assert {"alert", "severity", "clip"} <= result.keys()
        assert result["alert"].strip()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
