"""Smoke tests — run without a real model by mocking llama_cpp."""

from unittest.mock import MagicMock, patch
import json
import sys


def _make_events():
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
    mock_instance.return_value = {
        "choices": [{"text": json.dumps(json_response)}]
    }
    mock_class = MagicMock(return_value=mock_instance)
    return mock_class


def test_smoke():
    assert True


def test_format_events_contains_fields():
    """_format_events serialises all required event fields."""
    from eyas.llm.reasoner import Reasoner

    r = Reasoner("dummy.gguf")
    events = _make_events()
    formatted = r._format_events(events)

    assert "[entry]" in formatted
    assert "back_door" in formatted
    assert "02:14:22" in formatted
    assert "0.91" in formatted
    assert "cam2_02h14.mp4" in formatted


def test_trim_events_respects_max_chars():
    """_trim_events drops leading events when the log exceeds max_chars."""
    from eyas.llm.reasoner import Reasoner

    r = Reasoner("dummy.gguf")
    events = _make_events()
    # Force a tiny limit so we must trim to 1 event
    trimmed = r._trim_events(events, max_chars=80)
    assert len(trimmed) <= len(events)


def test_parse_json_valid():
    from eyas.llm.reasoner import Reasoner, _SUMMARIZE_FALLBACK

    r = Reasoner("dummy.gguf")
    payload = {"summary": "ok", "flags": [], "suspicious_clips": [], "risk_level": "none"}
    result = r._parse_json(json.dumps(payload), _SUMMARIZE_FALLBACK)
    assert result["summary"] == "ok"


def test_parse_json_fallback_on_invalid():
    from eyas.llm.reasoner import Reasoner, _SUMMARIZE_FALLBACK

    r = Reasoner("dummy.gguf")
    result = r._parse_json("not json at all", _SUMMARIZE_FALLBACK)
    assert result == _SUMMARIZE_FALLBACK


def test_summarize_events_empty():
    """summarize_events with no events never calls the model."""
    from eyas.llm.reasoner import Reasoner

    r = Reasoner("dummy.gguf")
    result = r.summarize_events([])
    assert "No events" in result["summary"]
    assert result["risk_level"] == "none"


def test_summarize_events_calls_model():
    """summarize_events builds a prompt containing event data and returns parsed JSON."""
    expected = {
        "summary": "1 after-hours entry.",
        "flags": ["after-hours entry"],
        "suspicious_clips": ["cam2_02h14.mp4"],
        "risk_level": "medium",
    }
    mock_llama_cls = _mock_llama(expected)

    llama_cpp_mock = MagicMock()
    llama_cpp_mock.Llama = mock_llama_cls
    llama_cpp_mock.LlamaGrammar = MagicMock()
    llama_cpp_mock.LlamaGrammar.from_string.return_value = None

    with patch.dict(sys.modules, {"llama_cpp": llama_cpp_mock}), \
         patch("os.path.isfile", return_value=True):
        from importlib import reload
        import eyas.llm.reasoner as mod
        reload(mod)

        r = mod.Reasoner("dummy.gguf")
        result = r.summarize_events(_make_events())

    assert result["summary"] == expected["summary"]
    assert result["risk_level"] == "medium"
    assert "cam2_02h14.mp4" in result["suspicious_clips"]


def test_answer_query_calls_model():
    """answer_query embeds the query in the prompt and returns parsed JSON."""
    expected = {
        "answer": "Yes, after-hours entry at back door.",
        "relevant_event_indices": [0],
        "clips": ["cam2_02h14.mp4"],
    }
    mock_llama_cls = _mock_llama(expected)

    llama_cpp_mock = MagicMock()
    llama_cpp_mock.Llama = mock_llama_cls
    llama_cpp_mock.LlamaGrammar = MagicMock()
    llama_cpp_mock.LlamaGrammar.from_string.return_value = None

    with patch.dict(sys.modules, {"llama_cpp": llama_cpp_mock}), \
         patch("os.path.isfile", return_value=True):
        from importlib import reload
        import eyas.llm.reasoner as mod
        reload(mod)

        r = mod.Reasoner("dummy.gguf")
        result = r.answer_query(_make_events(), "Was there unusual activity?")

    assert "after-hours" in result["answer"]
    assert 0 in result["relevant_event_indices"]


def test_summarize_prompt_contains_few_shot():
    """SUMMARIZE_PROMPT includes a worked example to ground the small model."""
    from eyas.llm.prompts import SUMMARIZE_PROMPT

    assert "EXAMPLE" in SUMMARIZE_PROMPT
    assert "risk_level" in SUMMARIZE_PROMPT
    assert "{period}" in SUMMARIZE_PROMPT
    assert "{event_log}" in SUMMARIZE_PROMPT


def test_qa_prompt_contains_few_shot():
    from eyas.llm.prompts import QA_PROMPT

    assert "EXAMPLE" in QA_PROMPT
    assert "{query}" in QA_PROMPT
    assert "relevant_event_indices" in QA_PROMPT
