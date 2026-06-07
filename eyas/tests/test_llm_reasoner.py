"""Tests for eyas/llm/reasoner.py — Reasoner class and module-level shims."""

import json
import sys
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

_REPO_ROOT = Path(__file__).parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import pytest

from eyas.llm.reasoner import Reasoner, _ALERT_FALLBACK, _QA_FALLBACK, _SUMMARIZE_FALLBACK

_W = 72


def _box(title: str, body: str) -> None:
    print(f"\n{'=' * _W}")
    print(f"  {title}")
    print(f"{'-' * _W}")
    for line in str(body).splitlines():
        print(textwrap.fill(line, width=_W - 4, initial_indent="  ", subsequent_indent="    ") if line.strip() else "")
    print(f"{'=' * _W}")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def two_events():
    return [
        {
            "type": "entry",
            "start_time": "02:14:22",
            "end_time": "02:14:35",
            "zone": "back_door",
            "metadata": {"confidence": 0.91, "clip_pointer": "cam2_02h14.mp4"},
        },
        {
            "type": "dwell",
            "start_time": "02:14:40",
            "end_time": "02:19:12",
            "zone": "aisle_3",
            "metadata": {"confidence": 0.87, "clip_pointer": "cam1_02h14.mp4"},
        },
    ]


def _mock_llama(json_response: dict):
    """Return a mock Llama class whose __call__ returns json_response as text."""
    mock_instance = MagicMock()
    mock_instance.return_value = {"choices": [{"text": json.dumps(json_response)}]}
    return MagicMock(return_value=mock_instance)


def _llama_module_mock(json_response: dict):
    m = MagicMock()
    m.Llama = _mock_llama(json_response)
    m.LlamaGrammar = MagicMock()
    m.LlamaGrammar.from_string.return_value = None
    return m


# ---------------------------------------------------------------------------
# _format_events
# ---------------------------------------------------------------------------

class TestFormatEvents:
    def test_contains_type(self, two_events):
        formatted = Reasoner("dummy.gguf")._format_events(two_events)
        _box(f"_format_events ({len(two_events)} events)", formatted)
        assert "[entry]" in formatted

    def test_contains_zone(self, two_events):
        assert "back_door" in Reasoner("dummy.gguf")._format_events(two_events)

    def test_contains_start_time(self, two_events):
        assert "02:14:22" in Reasoner("dummy.gguf")._format_events(two_events)

    def test_contains_confidence(self, two_events):
        assert "0.91" in Reasoner("dummy.gguf")._format_events(two_events)

    def test_contains_clip_pointer(self, two_events):
        assert "cam2_02h14.mp4" in Reasoner("dummy.gguf")._format_events(two_events)

    def test_empty_list_produces_empty_string(self):
        assert Reasoner("dummy.gguf")._format_events([]) == ""


# ---------------------------------------------------------------------------
# _trim_events
# ---------------------------------------------------------------------------

class TestTrimEvents:
    def test_no_trim_needed(self, two_events):
        r = Reasoner("dummy.gguf")
        assert r._trim_events(two_events, max_chars=9999) == two_events

    def test_trims_to_fit(self, two_events):
        r = Reasoner("dummy.gguf")
        trimmed = r._trim_events(two_events, max_chars=80)
        assert len(trimmed) < len(two_events)

    def test_always_returns_at_least_one(self, two_events):
        r = Reasoner("dummy.gguf")
        trimmed = r._trim_events(two_events, max_chars=1)
        assert len(trimmed) >= 1

    def test_empty_list_passthrough(self):
        r = Reasoner("dummy.gguf")
        assert r._trim_events([], max_chars=10) == []


# ---------------------------------------------------------------------------
# _parse_json
# ---------------------------------------------------------------------------

class TestParseJson:
    def test_valid_json_parsed(self):
        r = Reasoner("dummy.gguf")
        payload = {"summary": "ok", "flags": [], "suspicious_clips": [], "risk_level": "none"}
        assert r._parse_json(json.dumps(payload), _SUMMARIZE_FALLBACK)["summary"] == "ok"

    def test_invalid_json_returns_fallback(self):
        r = Reasoner("dummy.gguf")
        result = r._parse_json("not json at all", _SUMMARIZE_FALLBACK)
        assert result == _SUMMARIZE_FALLBACK

    def test_json_embedded_in_prose_is_extracted(self):
        r = Reasoner("dummy.gguf")
        raw = 'Sure! Here: {"answer": "yes", "relevant_event_indices": [], "clips": []} Done.'
        result = r._parse_json(raw, _QA_FALLBACK)
        assert result["answer"] == "yes"

    def test_fallback_is_a_copy_not_the_same_object(self):
        r = Reasoner("dummy.gguf")
        result = r._parse_json("bad", _SUMMARIZE_FALLBACK)
        result["summary"] = "mutated"
        assert _SUMMARIZE_FALLBACK["summary"] == ""


# ---------------------------------------------------------------------------
# summarize_events
# ---------------------------------------------------------------------------

class TestSummarizeEvents:
    def test_empty_events_skips_model(self):
        r = Reasoner("dummy.gguf")
        result = r.summarize_events([])
        _box(
            "summarize_events([]) empty-events fallback",
            f"summary:    {result['summary']}\nrisk_level: {result['risk_level']}",
        )
        assert "No events" in result["summary"]
        assert result["risk_level"] == "none"

    def test_calls_model_and_parses_response(self, two_events):
        expected = {
            "summary": "1 after-hours entry.",
            "flags": ["after-hours entry"],
            "suspicious_clips": ["cam2_02h14.mp4"],
            "risk_level": "medium",
        }
        with patch.dict(sys.modules, {"llama_cpp": _llama_module_mock(expected)}), \
             patch("os.path.isfile", return_value=True):
            from importlib import reload
            import eyas.llm.reasoner as mod
            reload(mod)
            r = mod.Reasoner("dummy.gguf")
            result = r.summarize_events(two_events)

        assert result["summary"] == expected["summary"]
        assert result["risk_level"] == "medium"
        assert "cam2_02h14.mp4" in result["suspicious_clips"]


# ---------------------------------------------------------------------------
# answer_query
# ---------------------------------------------------------------------------

class TestAnswerQuery:
    def test_empty_events_skips_model(self):
        r = Reasoner("dummy.gguf")
        result = r.answer_query([], "Anything unusual?")
        assert "No events" in result["answer"]

    def test_calls_model_and_parses_response(self, two_events):
        expected = {
            "answer": "Yes, after-hours entry at back door.",
            "relevant_event_indices": [0],
            "clips": ["cam2_02h14.mp4"],
        }
        with patch.dict(sys.modules, {"llama_cpp": _llama_module_mock(expected)}), \
             patch("os.path.isfile", return_value=True):
            from importlib import reload
            import eyas.llm.reasoner as mod
            reload(mod)
            r = mod.Reasoner("dummy.gguf")
            result = r.answer_query(two_events, "Anything unusual?")

        assert "after-hours" in result["answer"]
        assert 0 in result["relevant_event_indices"]


# ---------------------------------------------------------------------------
# generate_alert
# ---------------------------------------------------------------------------

class TestGenerateAlert:
    def test_calls_model_for_single_event(self, two_events):
        expected = {
            "alert": "After-hours entry at back door.",
            "severity": "medium",
            "clip": "cam2_02h14.mp4",
        }
        with patch.dict(sys.modules, {"llama_cpp": _llama_module_mock(expected)}), \
             patch("os.path.isfile", return_value=True):
            from importlib import reload
            import eyas.llm.reasoner as mod
            reload(mod)
            r = mod.Reasoner("dummy.gguf")
            result = r.generate_alert(two_events[0])

        assert result["alert"] == expected["alert"]
        assert result["severity"] == "medium"


# ---------------------------------------------------------------------------
# Model not found
# ---------------------------------------------------------------------------

class TestModelNotFound:
    def test_raises_runtime_error_if_file_missing(self):
        r = Reasoner("nonexistent_model.gguf")
        with pytest.raises(RuntimeError, match="not found"):
            r._load_model()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
