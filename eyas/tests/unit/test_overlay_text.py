"""Unit tests for utils.overlay_text."""

from __future__ import annotations

import numpy as np
import pytest

from postprocessing.translate_tts import TranslateStats, clear_translation_cache
from ui.locale import Strings
from utils.overlay_text import OverlayLabels, draw_text
from utils.paths import default_overlay_font


class TestOverlayLabels:
    def setup_method(self):
        clear_translation_cache()

    def test_english_person_label_with_description(self):
        labels = OverlayLabels("en")
        assert labels.person_label(3, "holding a bag") == "#3 holding a bag"

    def test_english_person_label_fallback(self):
        labels = OverlayLabels("en")
        assert labels.person_label(2, "") == "#2 person #2"

    def test_english_holding_and_pickup(self):
        labels = OverlayLabels("en")
        items = [{"count": 1, "name": "bottle"}]
        assert labels.holding_line(items) == "HOLDING: 1 x bottle"
        assert labels.pickup_line(items) == "PICKUP: 1 x bottle"

    def test_english_activity_known(self):
        labels = OverlayLabels("en")
        assert labels.activity_line("pickup") == "pickup"

    def test_korean_person_label_fixed_prefix(self):
        labels = OverlayLabels("ko")
        assert labels.person_label(1, "") == "#1 사람 #1"

    def test_korean_translates_dynamic_text(self, monkeypatch):
        def fake_translate_cached(text, target_lang="Korean", use_gpu=True):
            return f"KO:{text}", TranslateStats(cache_misses=1)

        monkeypatch.setattr(
            "postprocessing.translate_tts.translate_cached",
            fake_translate_cached,
        )
        labels = OverlayLabels("ko")
        assert labels.person_label(1, "a person") == "#1 KO:a person"
        assert labels.activity_line("reaching for shelf") == "KO:reaching for shelf"
        assert labels.holding_line([{"count": 1, "name": "bottle"}]) == (
            "소지: 1 x KO:bottle"
        )

    def test_korean_known_activity_not_translated(self, monkeypatch):
        calls: list[str] = []

        def fake_translate_cached(text, target_lang="Korean", use_gpu=True):
            calls.append(text)
            return f"KO:{text}", TranslateStats(cache_misses=1)

        monkeypatch.setattr(
            "postprocessing.translate_tts.translate_cached",
            fake_translate_cached,
        )
        labels = OverlayLabels("ko")
        assert labels.activity_line("pickup") == "집기"
        assert calls == []

    def test_korean_translate_failure_returns_original(self, monkeypatch):
        def failing_translate_cached(text, target_lang="Korean", use_gpu=True):
            raise RuntimeError("translation unavailable")

        monkeypatch.setattr(
            "postprocessing.translate_tts.translate_cached",
            failing_translate_cached,
        )
        labels = OverlayLabels("ko")
        assert labels.person_label(1, "a person") == "#1 a person"


class TestDrawText:
    @pytest.fixture(autouse=True)
    def _require_font(self):
        if not default_overlay_font().is_file():
            pytest.skip("bundled overlay font missing")

    def test_draw_text_smoke(self):
        frame = np.zeros((64, 128, 3), dtype=np.uint8)
        draw_text(frame, "test", (4, 20), (0, 255, 0))
        draw_text(frame, "집기", (4, 40), (0, 0, 255), font_height=14)
        assert frame.any()

    def test_draw_text_korean_changes_pixels(self):
        frame = np.zeros((64, 128, 3), dtype=np.uint8)
        before = frame.copy()
        draw_text(frame, "집기", (4, 40), (0, 0, 255), font_height=14)
        assert not np.array_equal(frame, before)


class TestOverlayLocaleKeys:
    def test_overlay_keys_exist(self):
        for locale in ("en", "ko"):
            s = Strings(locale)
            assert s.t("overlay.person", id=1)
            assert s.t("overlay.holding")
            assert s.t("overlay.pickup")

    def test_korean_overlay_prefix_values(self):
        s = Strings("ko")
        assert s.t("overlay.holding") == "소지"
        assert s.t("overlay.pickup") == "집기"
