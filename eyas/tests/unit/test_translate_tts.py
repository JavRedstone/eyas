"""Unit tests for eyas.postprocessing.translate_tts.

Mocked, fast tests — no model weights or GPU required.

Run:
    pytest eyas/tests/unit/test_translate_tts.py -v
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

import eyas.postprocessing as postprocessing
from eyas.postprocessing.translate_tts import (
    _looks_like_meta_response,
    clear_translation_cache,
    translate,
    translate_cached,
    translate_many,
    tts,
)

SOURCE_EN = (
    "The man is walking and moving through the store, with slight changes in "
    "posture suggesting progression or adjustment of position."
)
META_GARBAGE = (
    "이 문장은 이미 한국어로 작성되어 있습니다. "
    '영어로 번역하면 다음과 같습니다: "The man is walking..."'
)
CLEAN_KO = (
    "남자가 상점을 걸으며 이동하고 있으며, "
    "자세의 미묘한 변화는 진행 또는 위치 조정을 암시합니다."
)


def _mock_tinyaya_response(content: str = "  안녕  ") -> MagicMock:
    model = MagicMock()
    model.create_chat_completion.return_value = {
        "choices": [{"message": {"content": content}}]
    }
    return model


def _mock_voxcpm2_model(sample_rate: int = 48000) -> tuple[MagicMock, int]:
    model = MagicMock()

    def _stream(*, text: str):
        del text
        yield np.array([0.1, -0.2, 0.3], dtype=np.float64)

    model.generate_streaming.side_effect = _stream
    return model, sample_rate


# ---------------------------------------------------------------------------
# Validation (no mocks — fails before model load)
# ---------------------------------------------------------------------------


class TestTranslateValidation:
    def test_rejects_unsupported_target_lang(self):
        with pytest.raises(ValueError, match="Klingon"):
            translate("hello", target_lang="Klingon")


class TestTtsValidation:
    def test_rejects_empty_text(self):
        with pytest.raises(ValueError, match="Text is empty"):
            list(tts(""))

    def test_rejects_whitespace_only(self):
        with pytest.raises(ValueError, match="Text is empty"):
            list(tts("   \n\t  "))

    def test_rejects_unsupported_target_lang(self):
        with pytest.raises(ValueError, match="Klingon"):
            list(tts("Hello", target_lang="Klingon"))


# ---------------------------------------------------------------------------
# translate() prompt / format (mocked)
# ---------------------------------------------------------------------------


class TestTranslatePrompt:
    @patch("eyas.postprocessing.translate_tts.get_tinyaya_model")
    def test_strips_model_output(self, mock_get_model):
        mock_get_model.return_value = _mock_tinyaya_response("  안녕  ")
        assert translate("hello", target_lang="Korean") == "안녕"

    @patch("eyas.postprocessing.translate_tts.get_tinyaya_model")
    def test_passes_chat_completion_args(self, mock_get_model):
        mock_get_model.return_value = _mock_tinyaya_response("translated")
        translate("hello", target_lang="Korean")

        mock_get_model.assert_called_once_with(use_gpu=True)
        mock_get_model.return_value.create_chat_completion.assert_called_once_with(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a translation engine. "
                        "Output only the translated text. "
                        "No explanations, notes, or language detection."
                    ),
                },
                {
                    "role": "user",
                    "content": "Translate to Korean:\nhello",
                },
            ],
            max_tokens=4096,
            temperature=0,
            top_p=0.95,
        )

    @patch("eyas.postprocessing.translate_tts.get_tinyaya_model")
    def test_use_gpu_false_is_forwarded(self, mock_get_model):
        mock_get_model.return_value = _mock_tinyaya_response("translated")
        translate("hello", target_lang="Korean", use_gpu=False)
        mock_get_model.assert_called_once_with(use_gpu=False)


class TestMetaResponseValidation:
    def test_clean_korean_is_valid(self):
        assert not _looks_like_meta_response(SOURCE_EN, CLEAN_KO)

    def test_clean_english_is_valid(self):
        assert not _looks_like_meta_response("bonjour", "hello")

    def test_meta_garbage_is_invalid(self):
        assert _looks_like_meta_response(SOURCE_EN, META_GARBAGE)


class TestTranslateRetry:
    @patch("eyas.postprocessing.translate_tts.get_tinyaya_model")
    def test_meta_response_triggers_retry(self, mock_get_model):
        model = MagicMock()
        model.create_chat_completion.side_effect = [
            {"choices": [{"message": {"content": META_GARBAGE}}]},
            {"choices": [{"message": {"content": CLEAN_KO}}]},
        ]
        mock_get_model.return_value = model

        assert translate(SOURCE_EN, target_lang="Korean") == CLEAN_KO
        assert model.create_chat_completion.call_count == 2

    @patch("eyas.postprocessing.translate_tts.get_tinyaya_model")
    def test_invalid_retry_returns_source(self, mock_get_model):
        model = MagicMock()
        model.create_chat_completion.side_effect = [
            {"choices": [{"message": {"content": META_GARBAGE}}]},
            {"choices": [{"message": {"content": META_GARBAGE}}]},
        ]
        mock_get_model.return_value = model

        assert translate(SOURCE_EN, target_lang="Korean") == SOURCE_EN
        assert model.create_chat_completion.call_count == 2

    @patch("eyas.postprocessing.translate_tts.get_tinyaya_model")
    def test_valid_first_response_no_retry(self, mock_get_model):
        mock_get_model.return_value = _mock_tinyaya_response(CLEAN_KO)

        assert translate(SOURCE_EN, target_lang="Korean") == CLEAN_KO
        mock_get_model.return_value.create_chat_completion.assert_called_once()


class TestTranslateCaching:
    def test_reuses_model_for_same_use_gpu(self):
        postprocessing._tinyaya_models.clear()
        try:
            sentinel = MagicMock(name="tinyaya-instance")
            postprocessing._tinyaya_models[True] = sentinel
            assert postprocessing.get_tinyaya_model(use_gpu=True) is sentinel
        finally:
            postprocessing._tinyaya_models.clear()


# ---------------------------------------------------------------------------
# tts() voice wiring (mocked)
# ---------------------------------------------------------------------------


class TestTtsVoiceWiring:
    @patch("eyas.postprocessing.translate_tts.get_voxcpm2_model")
    def test_default_voice_prefix(self, mock_get_voxcpm):
        model, sample_rate = _mock_voxcpm2_model()
        mock_get_voxcpm.return_value = (model, sample_rate)

        chunks = list(tts("Hello", target_lang="English"))

        model.generate_streaming.assert_called_once_with(
            text="(A young woman, gentle and sweet voice)Hello"
        )
        assert len(chunks) == 1
        assert chunks[0][0] == sample_rate
        assert chunks[0][1].dtype == np.float32

    @patch("eyas.postprocessing.translate_tts.get_voxcpm2_model")
    def test_empty_voice_omits_prefix(self, mock_get_voxcpm):
        model, sample_rate = _mock_voxcpm2_model()
        mock_get_voxcpm.return_value = (model, sample_rate)

        list(tts("Hello", target_lang="English", voice=""))

        model.generate_streaming.assert_called_once_with(text="Hello")

    @patch("eyas.postprocessing.translate_tts.get_voxcpm2_model")
    def test_custom_voice_prefix(self, mock_get_voxcpm):
        model, sample_rate = _mock_voxcpm2_model()
        mock_get_voxcpm.return_value = (model, sample_rate)

        list(tts("Hello", target_lang="English", voice="A deep male narrator voice"))

        model.generate_streaming.assert_called_once_with(
            text="(A deep male narrator voice)Hello"
        )

    @patch("eyas.postprocessing.translate_tts.get_voxcpm2_model")
    def test_forwards_all_streaming_chunks(self, mock_get_voxcpm):
        model = MagicMock()
        sample_rate = 48000
        raw_chunks = [
            np.array([0.1, -0.2], dtype=np.float64),
            np.array([0.3], dtype=np.float64),
            np.array([0.4, 0.5, -0.6], dtype=np.float64),
        ]

        def _stream(*, text: str):
            del text
            yield from raw_chunks

        model.generate_streaming.side_effect = _stream
        mock_get_voxcpm.return_value = (model, sample_rate)

        chunks = list(tts("Hello", target_lang="English"))

        assert len(chunks) == len(raw_chunks)
        for (rate, audio), raw in zip(chunks, raw_chunks):
            assert rate == sample_rate
            assert audio.dtype == np.float32
            np.testing.assert_array_equal(audio, raw.astype(np.float32))


# ---------------------------------------------------------------------------
# translate_cached / translate_many
# ---------------------------------------------------------------------------


class TestTranslateCache:
    def setup_method(self):
        clear_translation_cache()

    @patch("eyas.postprocessing.translate_tts.translate")
    def test_cache_miss_calls_translate(self, mock_translate):
        mock_translate.return_value = "안녕"
        result, stats = translate_cached("hello", target_lang="Korean")
        assert result == "안녕"
        assert stats.cache_misses == 1
        assert stats.cache_hits == 0
        assert stats.elapsed_s >= 0
        mock_translate.assert_called_once_with("hello", target_lang="Korean", use_gpu=True)

    @patch("eyas.postprocessing.translate_tts.translate")
    def test_cache_hit_skips_translate(self, mock_translate):
        mock_translate.return_value = "안녕"
        translate_cached("hello", target_lang="Korean")
        result, stats = translate_cached("hello", target_lang="Korean")
        assert result == "안녕"
        assert stats.cache_hits == 1
        assert stats.cache_misses == 0
        assert stats.elapsed_s == 0
        mock_translate.assert_called_once()

    @patch("eyas.postprocessing.translate_tts.translate")
    def test_translate_many_dedupes_and_aggregates(self, mock_translate):
        mock_translate.side_effect = lambda text, **kwargs: f"ko:{text}"
        mapping, stats = translate_many({"a", "b"}, "Korean")
        assert mapping == {"a": "ko:a", "b": "ko:b"}
        assert stats.cache_misses == 2
        assert stats.cache_hits == 0

        mapping2, stats2 = translate_many({"a"}, "Korean")
        assert mapping2["a"] == "ko:a"
        assert stats2.cache_hits == 1
        assert stats2.cache_misses == 0
        assert mock_translate.call_count == 2

    @patch("eyas.postprocessing.translate_tts.translate")
    def test_does_not_cache_invalid_result(self, mock_translate):
        mock_translate.return_value = SOURCE_EN
        translate_cached(SOURCE_EN, target_lang="Korean")
        translate_cached(SOURCE_EN, target_lang="Korean")
        assert mock_translate.call_count == 2
