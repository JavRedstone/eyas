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
    display_risk,
    display_zone,
    format_translation_time,
    is_known_activity,
    localize_llm_result,
    localize_text,
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
        assert len(Strings("en").table_headers()) == 7

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
