"""Integration tests for eyas.postprocessing.translate_tts.

Requires HuggingFace model access, llama-cpp-python, and voxcpm.
TTS streaming and translate→TTS pipeline tests require CUDA.

Run:
    pytest eyas/tests/module/test_translate_tts.py -v
"""

from __future__ import annotations

import numpy as np
import pytest
import torch

pytest.importorskip("llama_cpp")
pytest.importorskip("voxcpm")

from eyas.postprocessing import get_voxcpm2_model
from eyas.postprocessing.translate_tts import translate, tts

requires_cuda = pytest.mark.skipif(
    not torch.cuda.is_available(),
    reason="CUDA required for VoxCPM2 TTS streaming tests",
)

LONG_ALERT = (
    "Suspicious activity detected at shelf A. "
    "Person loitering near the back door for over three minutes. "
    "Confidence score 0.91 at 02:14 AM."
)


def _assert_valid_audio_stream(
    chunks: list[tuple[int, np.ndarray]],
    *,
    expected_sample_rate: int | None = None,
    min_duration: float = 0.1,
) -> None:
    """Check streamed TTS chunks have the expected shape and sample rate."""
    assert len(chunks) >= 1

    expected_rate = expected_sample_rate if expected_sample_rate is not None else chunks[0][0]
    total_samples = 0
    for sample_rate, audio in chunks:
        assert sample_rate == expected_rate
        assert isinstance(audio, np.ndarray)
        assert audio.dtype == np.float32
        assert audio.ndim == 1
        assert audio.size > 0
        assert np.all(audio >= -1.0)
        assert np.all(audio <= 1.0)
        total_samples += audio.size

    assert total_samples / expected_rate >= min_duration


# ---------------------------------------------------------------------------
# translate() — real model
# ---------------------------------------------------------------------------


class TestTranslate:
    def test_translate_to_korean_changes_output(self):
        source = "Hello, how are you?"
        result = translate(source, target_lang="Korean")

        assert result
        assert result.strip() != source
        assert "Translate the following" not in result

    def test_translate_default_english(self):
        result = translate("Bonjour, comment allez-vous?")

        assert result
        assert isinstance(result, str)

    def test_accepts_supported_target_lang(self):
        result = translate("hello", target_lang="Korean")

        assert result
        assert isinstance(result, str)

    def test_translate_use_gpu_false(self):
        result = translate("hello", target_lang="Korean", use_gpu=False)

        assert result
        assert isinstance(result, str)

    def test_translate_long_alert_text(self):
        result = translate(LONG_ALERT, target_lang="English")

        assert result
        assert "Translate the following" not in result


# ---------------------------------------------------------------------------
# tts() — validation (no CUDA)
# ---------------------------------------------------------------------------


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
# tts() — streaming (CUDA)
# ---------------------------------------------------------------------------


@requires_cuda
class TestTtsStreaming:
    def test_streams_korean_audio(self):
        chunks = list(tts("안녕하세요", target_lang="Korean"))
        _assert_valid_audio_stream(chunks)

    def test_streams_english_with_default_voice(self):
        chunks = list(tts("Hello", target_lang="English"))
        _assert_valid_audio_stream(chunks)

    def test_streams_with_custom_voice(self):
        chunks = list(tts("Hello", target_lang="English", voice="A deep male narrator voice"))
        _assert_valid_audio_stream(chunks)

    def test_streams_with_empty_voice(self):
        chunks = list(tts("Hello", target_lang="English", voice=""))
        _assert_valid_audio_stream(chunks)

    def test_sample_rate_matches_model(self):
        _, expected_rate = get_voxcpm2_model()
        chunks = list(tts("Hello", target_lang="English"))
        _assert_valid_audio_stream(chunks, expected_sample_rate=expected_rate)

    def test_longer_text_yields_multiple_chunks(self):
        long_text = "This is a longer English alert message for streaming coverage. " * 3
        chunks = list(tts(long_text, target_lang="English"))
        assert len(chunks) >= 1
        _assert_valid_audio_stream(chunks)

    def test_english_summary_concatenates_to_audio(self):
        chunks = list(tts(LONG_ALERT, target_lang="English"))
        assert len(chunks) >= 1

        sample_rate = chunks[0][0]
        audio = np.concatenate([chunk for _, chunk in chunks])

        assert audio.dtype == np.float32
        assert audio.ndim == 1
        assert audio.size > 0
        assert np.all(audio >= -1.0)
        assert np.all(audio <= 1.0)
        assert audio.size / sample_rate >= 0.1


# ---------------------------------------------------------------------------
# Language coverage
# ---------------------------------------------------------------------------


class TestLanguageCoverage:
    def test_translate_welsh_supported(self):
        result = translate("hello", target_lang="Welsh")
        assert result
        assert isinstance(result, str)

    def test_tts_welsh_unsupported(self):
        with pytest.raises(ValueError, match="Welsh"):
            list(tts("Hello", target_lang="Welsh"))


# ---------------------------------------------------------------------------
# translate → tts pipeline (CUDA)
# ---------------------------------------------------------------------------


@requires_cuda
class TestTranslateTtsPipeline:
    def test_alert_translate_then_speak_korean(self):
        source = "Suspicious activity detected at shelf A."
        korean = translate(source, target_lang="Korean")

        assert korean
        assert korean.strip() != source

        chunks = list(tts(korean, target_lang="Korean"))
        _assert_valid_audio_stream(chunks)
