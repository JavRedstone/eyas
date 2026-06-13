"""Unit tests for eyas.ui.locale."""

from __future__ import annotations

import pytest

from postprocessing.translate_tts import TranslateStats, clear_translation_cache
from ui.locale import (
    MESSAGES,
    REQUIRED_MESSAGE_KEYS,
    Strings,
    batch_translate_freeform,
    display_activity,
    display_event_type,
    display_risk,
    display_zone,
    format_event_row,
    format_translation_time,
    is_known_activity,
    is_known_zone,
    localize_chat_for_display,
    localize_events_for_display,
    localize_llm_result,
    localize_summary_for_display,
    localize_text,
    localize_zone_labels,
    pipeline_steps_default,
)


class TestMessageCatalog:
    def test_en_and_ko_have_same_keys(self):
        en_keys = set(MESSAGES["en"].keys())
        ko_keys = set(MESSAGES["ko"].keys())
        assert en_keys == ko_keys
        assert en_keys == set(REQUIRED_MESSAGE_KEYS)

    def test_all_required_keys_resolve(self):
        for locale in ("en", "ko"):
            s = Strings(locale)
            for key in REQUIRED_MESSAGE_KEYS:
                text = s.t(key)
                assert text and text != key


class TestStrings:
    def test_english_lookup(self):
        s = Strings("en")
        assert s.t("buttons.analyze") == "Analyze"

    def test_korean_lookup(self):
        s = Strings("ko")
        assert s.t("buttons.analyze") == "분석"

    def test_format_kwargs(self):
        s = Strings("en")
        assert "42" in s.t("status.done", frames=42, tracks=3, events=1)

    def test_unknown_locale_falls_back_to_en(self):
        s = Strings("fr")
        assert s.locale == "en"

    def test_table_headers_count(self):
        assert len(Strings("en").table_headers()) == 8

    def test_korean_table_headers(self):
        headers = Strings("ko").table_headers()
        assert "이벤트" in headers
        assert "활동" in headers
        assert "구역" in headers

    def test_tts_lang(self):
        assert Strings("ko").tts_lang == "Korean"
        assert Strings("en").tts_lang == "English"


class TestDisplayHelpers:
    def test_display_zone_known(self):
        assert display_zone("back_door", "ko") == "뒷문"

    def test_display_zone_unknown_passthrough(self):
        assert display_zone("custom_zone", "ko") == "custom_zone"

    def test_display_activity_known(self):
        assert display_activity("pickup", "ko") == "집기"

    def test_display_event_type(self):
        assert display_event_type("observation", "ko") == "관찰"
        assert display_event_type("pickup", "en") == "pickup"

    def test_display_activity_unknown_passthrough(self):
        assert display_activity("browsing shelves", "ko") == "browsing shelves"

    def test_display_risk(self):
        assert display_risk("medium", "ko") == "중간"

    def test_is_known_activity(self):
        assert is_known_activity("pickup")
        assert not is_known_activity("looking at shelf")


class TestPipelineSteps:
    def test_default_steps_use_stable_ids(self):
        steps = pipeline_steps_default()
        assert len(steps) == 4
        assert steps[0][0] == "load_video"
        assert all(state == "pending" for _, state, _ in steps)


class TestBatchTranslate:
    def setup_method(self):
        clear_translation_cache()

    def test_english_is_identity(self):
        texts = {"walking", "standing"}
        result, stats = batch_translate_freeform(texts, "en")
        assert result == {"walking": "walking", "standing": "standing"}
        assert stats is None

    def test_korean_skips_known_activities(self, monkeypatch):
        calls: list[str] = []

        def fake_translate(text, target_lang="Korean", use_gpu=True):
            calls.append(text)
            return f"번역:{text}"

        monkeypatch.setattr(
            "postprocessing.translate_tts.translate",
            fake_translate,
        )
        result, stats = batch_translate_freeform({"pickup", "walking near shelf"}, "ko")
        assert result["pickup"] == "pickup"
        assert result["walking near shelf"] == "번역:walking near shelf"
        assert calls == ["walking near shelf"]
        assert stats is not None
        assert stats.cache_misses == 1


class TestLocalizeHelpers:
    def setup_method(self):
        clear_translation_cache()

    def test_localize_text_english_passthrough(self):
        text, stats = localize_text("hello", "en")
        assert text == "hello"
        assert stats is None

    def test_format_translation_time_empty_when_no_stats(self):
        assert format_translation_time(Strings("en"), None) == ""

    def test_format_translation_time_shows_stats(self):
        s = Strings("en")
        stats = TranslateStats(elapsed_s=1.23, cache_hits=2, cache_misses=1)
        formatted = format_translation_time(s, stats)
        assert "1.23" in formatted
        assert "2" in formatted
        assert "1" in formatted

    def test_localize_llm_result_translates_summary_and_flags(self, monkeypatch):
        def fake_translate(text, target_lang="Korean", use_gpu=True):
            return f"KO:{text}"

        monkeypatch.setattr(
            "postprocessing.translate_tts.translate",
            fake_translate,
        )
        llm = {
            "summary": "Alert summary",
            "flags": ["after-hours entry"],
            "risk_level": "medium",
        }
        result, stats = localize_llm_result(llm, "ko")
        assert result["summary"] == "KO:Alert summary"
        assert result["flags"] == ["KO:after-hours entry"]
        assert result["risk_level"] == "medium"
        assert stats is not None
        assert stats.cache_misses == 2


class TestFormatEventRow:
    def setup_method(self):
        clear_translation_cache()

    def test_english_row(self):
        ev = {
            "pickup_confirmed": False,
            "activity": "entry",
            "timestamp": 65.0,
            "confirmation_timestamp": None,
            "zone": "back_door",
            "confidence": 0.94,
        }
        row = format_event_row(ev, 0, Strings("en"), text_cache={})
        assert row[1] == "observation"
        assert row[2] == "entry"
        assert row[5] == "Back Door"

    def test_korean_row_catalog_labels(self):
        ev = {
            "pickup_confirmed": True,
            "activity": "walking",
            "timestamp": 10.0,
            "confirmation_timestamp": 12.0,
            "zone": "review_area",
            "confidence": 0.88,
            "picked_up_items": [{"name": "bottle", "count": 1}],
        }
        cache: dict[str, str] = {}

        def fake_localize(text, locale):
            return f"KO:{text}", None

        import ui.locale as locale_mod

        original = locale_mod.localize_text
        locale_mod.localize_text = fake_localize
        try:
            row = format_event_row(ev, 0, Strings("ko"), text_cache=cache)
        finally:
            locale_mod.localize_text = original

        assert row[1] == "집기"
        assert row[2] == "집기"
        assert row[5] == "검토 구역"
        assert row[7] == "KO:bottle"


class TestLocalizeEventsForDisplay:
    def setup_method(self):
        clear_translation_cache()

    def test_english_passthrough(self):
        ev = {"description": "person walking", "zone": "entrance"}
        result, stats = localize_events_for_display([ev], "en")
        assert result[0] == ev
        assert "description_ko" not in result[0]
        assert stats is None

    def test_korean_known_zone_catalog(self, monkeypatch):
        def fake_translate(text, target_lang="Korean", use_gpu=True):
            return f"KO:{text}"

        monkeypatch.setattr("postprocessing.translate_tts.translate", fake_translate)
        ev = {
            "description": "person at door",
            "zone": "entrance",
        }
        result, stats = localize_events_for_display([ev], "ko")
        assert result[0]["zone_ko"] == "입구"
        assert result[0]["description_ko"] == "KO:person at door"
        assert stats is not None

    def test_korean_unknown_zone_translated(self, monkeypatch):
        def fake_translate(text, target_lang="Korean", use_gpu=True):
            return f"KO:{text}"

        monkeypatch.setattr("postprocessing.translate_tts.translate", fake_translate)
        ev = {"description": "activity", "zone": "custom_zone"}
        result, _ = localize_events_for_display([ev], "ko")
        assert result[0]["zone_ko"] == "KO:custom_zone"


class TestLocalizeZoneLabels:
    def setup_method(self):
        clear_translation_cache()

    def test_english_identity(self):
        mapping, stats = localize_zone_labels(["entrance", "custom"], "en")
        assert mapping == {"entrance": "entrance", "custom": "custom"}
        assert stats is None

    def test_korean_known_and_unknown(self, monkeypatch):
        def fake_translate(text, target_lang="Korean", use_gpu=True):
            return f"KO:{text}"

        monkeypatch.setattr("postprocessing.translate_tts.translate", fake_translate)
        mapping, stats = localize_zone_labels(["entrance", "custom_zone"], "ko")
        assert mapping["entrance"] == "입구"
        assert mapping["custom_zone"] == "KO:custom_zone"
        assert stats is not None

    def test_korean_camera_zones_use_catalog_not_llm(self, monkeypatch):
        def fake_translate(text, target_lang="Korean", use_gpu=True):
            raise AssertionError(f"camera zone should not be translated: {text}")

        monkeypatch.setattr("postprocessing.translate_tts.translate", fake_translate)
        mapping, stats = localize_zone_labels(["cam1", "cam2", "cam3", "cam4"], "ko")
        assert mapping == {
            "cam1": "카메라 1",
            "cam2": "카메라 2",
            "cam3": "카메라 3",
            "cam4": "카메라 4",
        }
        assert stats is None

    def test_is_known_zone(self):
        assert is_known_zone("back_door")
        assert is_known_zone("cam2")
        assert not is_known_zone("custom_zone")


class TestLocalizeSummaryForDisplay:
    def setup_method(self):
        clear_translation_cache()

    def test_english_passthrough(self):
        summary = {"summary": "Overnight was quiet.", "flags": ["loitering near door"]}
        result, stats = localize_summary_for_display(summary, "en")
        assert result["summary"] == "Overnight was quiet."
        assert "summary_ko" not in result
        assert stats is None

    def test_korean_adds_ko_fields(self, monkeypatch):
        def fake_translate(text, target_lang="Korean", use_gpu=True):
            return f"KO:{text}"

        monkeypatch.setattr("postprocessing.translate_tts.translate", fake_translate)
        summary = {"summary": "Overnight was quiet.", "flags": ["loitering near door"]}
        result, stats = localize_summary_for_display(summary, "ko")
        assert result["summary"] == "Overnight was quiet."
        assert result["summary_ko"] == "KO:Overnight was quiet."
        assert result["flags"] == ["loitering near door"]
        assert result["flags_ko"] == ["KO:loitering near door"]
        assert stats is not None


class TestLocalizeChatForDisplay:
    def setup_method(self):
        clear_translation_cache()

    def test_english_passthrough(self):
        messages = [
            {"role": "user", "text": "Anything unusual?"},
            {"role": "assistant", "text": "No issues detected."},
        ]
        result, stats = localize_chat_for_display(messages, "en")
        assert result == messages
        assert stats is None

    def test_korean_translates_assistant_only(self, monkeypatch):
        def fake_translate(text, target_lang="Korean", use_gpu=True):
            return f"KO:{text}"

        monkeypatch.setattr("postprocessing.translate_tts.translate", fake_translate)
        messages = [
            {"role": "user", "text": "Anything unusual?"},
            {"role": "assistant", "text": "No issues detected."},
        ]
        result, stats = localize_chat_for_display(messages, "ko")
        assert result[0]["text"] == "Anything unusual?"
        assert "text_ko" not in result[0]
        assert result[1]["text"] == "No issues detected."
        assert result[1]["text_ko"] == "KO:No issues detected."
        assert stats is not None
