"""Smoke tests — validate the whole system is importable and wired up.

Run this first. If anything here fails, the module-specific test files
will tell you exactly what broke.
"""

# ---------------------------------------------------------------------------
# Module imports
# ---------------------------------------------------------------------------

def test_storage_imports():
    import eyas.storage.manager as m
    assert callable(m.store)
    assert callable(m.list_clips)
    assert callable(m.choices)
    assert callable(m.path_from_choice)
    assert callable(m.delete)


def test_streaming_imports():
    from eyas.streaming.capture import default_capture
    assert hasattr(default_capture, "start")
    assert hasattr(default_capture, "stop")
    assert hasattr(default_capture, "get_rgb")
    assert hasattr(default_capture, "start_recording")
    assert hasattr(default_capture, "stop_recording")


def test_llm_prompts_imports():
    from eyas.llm.prompts import (
        SYSTEM_PROMPT, SUMMARIZE_PROMPT, QA_PROMPT, ALERT_PROMPT,
        SUMMARIZE_GRAMMAR, QA_GRAMMAR, ALERT_GRAMMAR,
    )
    for obj in (SYSTEM_PROMPT, SUMMARIZE_PROMPT, QA_PROMPT, ALERT_PROMPT,
                SUMMARIZE_GRAMMAR, QA_GRAMMAR, ALERT_GRAMMAR):
        assert isinstance(obj, str) and obj


def test_llm_reasoner_imports():
    from eyas.llm.reasoner import Reasoner, summarize_events, answer_query
    assert callable(summarize_events)
    assert callable(answer_query)
    r = Reasoner("dummy.gguf")
    assert callable(r.summarize_events)
    assert callable(r.answer_query)
    assert callable(r.generate_alert)


def test_event_structuring_imports():
    from eyas.event_structuring.structurer import build_events
    assert callable(build_events)


def test_object_detection_imports():
    from eyas.object_detection.detector import detect_objects
    assert callable(detect_objects)


def test_video_processing_imports():
    from eyas.video_processing.process import process_clip
    assert callable(process_clip)


# ---------------------------------------------------------------------------
# Gradio app builds without error
# ---------------------------------------------------------------------------

def test_gradio_app_builds():
    from eyas.ui.gradio_app import EyasTheme, build_app
    theme = EyasTheme(color="night", dark=True)
    assert theme.name == "eyas-night-dark"
    app = build_app(color="night", dark=True)
    assert app is not None


def test_all_four_themes_build():
    from eyas.ui.gradio_app import EyasTheme
    for color in ("night", "amber", "cyber", "sentinel"):
        for dark in (True, False):
            t = EyasTheme(color=color, dark=dark)
            assert t.name.startswith("eyas-")


# ---------------------------------------------------------------------------
# Pipeline interfaces are callable with minimal inputs
# ---------------------------------------------------------------------------

def test_reasoner_empty_events_no_model_needed():
    from eyas.llm.reasoner import Reasoner
    r = Reasoner("dummy.gguf")
    result = r.summarize_events([])
    assert isinstance(result, dict)
    assert "summary" in result
    assert "risk_level" in result

    result = r.answer_query([], "Anything unusual?")
    assert isinstance(result, dict)
    assert "answer" in result


def test_storage_round_trip(tmp_path, monkeypatch):
    import eyas.storage.manager as m
    monkeypatch.setattr(m, "_CLIPS", tmp_path / "clips")
    monkeypatch.setattr(m, "_INDEX", tmp_path / "index.json")

    dummy = tmp_path / "clip.mp4"
    dummy.write_bytes(b"\x00" * 512)

    entry = m.store(str(dummy))
    assert entry["filename"]
    assert m.list_clips()
    assert m.choices()
    assert m.path_from_choice(m.choices()[0])
    assert m.delete(entry["filename"])
    assert m.list_clips() == []
