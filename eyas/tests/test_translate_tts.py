"""Tests for eyas.postprocessing.translate_tts.

Requires HuggingFace model access, llama-cpp-python, and voxcpm (CUDA for TTS).

Run:
    pytest eyas/tests/test_translate_tts.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import torch

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

pytest.importorskip("llama_cpp")
pytest.importorskip("voxcpm")

from eyas.postprocessing.translate_tts import translate, tts

requires_cuda = pytest.mark.skipif(
    not torch.cuda.is_available(),
    reason="CUDA required to run VoxCPM2 TTS model tests",
)


def _assert_valid_audio_stream(chunks: list[tuple[int, np.ndarray]], min_duration: float = 0.1) -> None:
    """Check streamed TTS chunks have the expected shape and sample rate."""
    assert len(chunks) >= 1

    total_samples = 0
    expected_sample_rate = chunks[0][0]
    for sample_rate, audio in chunks:
        assert sample_rate == expected_sample_rate
        assert isinstance(audio, np.ndarray)
        assert audio.dtype == np.float32
        assert audio.ndim == 1
        assert audio.size > 0
        assert np.all(audio >= -1.0)
        assert np.all(audio <= 1.0)
        total_samples += audio.size

    assert total_samples / expected_sample_rate >= min_duration


# ---------------------------------------------------------------------------
# translate()
# ---------------------------------------------------------------------------


class TestTranslate:
    def test_rejects_unsupported_target_lang(self):
        """Unsupported target_lang raises ValueError before generation."""
        with pytest.raises(ValueError, match="Klingon"):
            translate("hello", target_lang="Klingon")

    def test_translate_to_korean_changes_output(self):
        """English input is translated to Korean without prompt leakage."""
        source = "Hello, how are you?"
        result = translate(source, target_lang="Korean")

        assert result
        assert result.strip() != source
        assert "Translate the following" not in result

    def test_translate_default_english(self):
        """Default target_lang produces non-empty English output."""
        result = translate("Bonjour, comment allez-vous?")

        assert result
        assert isinstance(result, str)

    def test_accepts_supported_target_lang(self):
        """Supported target_lang returns a non-empty translated string."""
        result = translate("hello", target_lang="Korean")

        assert result
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# tts()
# ---------------------------------------------------------------------------


@requires_cuda
class TestTts:
    def test_rejects_empty_text(self):
        """Empty text raises ValueError."""
        with pytest.raises(ValueError, match="Text is empty"):
            list(tts(""))

    def test_rejects_whitespace_only(self):
        """Whitespace-only text raises ValueError."""
        with pytest.raises(ValueError, match="Text is empty"):
            list(tts("   \n\t  "))

    def test_rejects_unsupported_target_lang(self):
        """Unsupported target_lang raises ValueError before generation."""
        with pytest.raises(ValueError, match="Klingon"):
            list(tts("Hello", target_lang="Klingon"))

    def test_streams_korean_audio(self):
        """Korean text streams audio chunks at the expected sample rate."""
        chunks = list(tts("안녕하세요", target_lang="Korean"))
        _assert_valid_audio_stream(chunks)

    def test_streams_english_with_default_voice(self):
        """English text streams audio with the default voice settings."""
        chunks = list(tts("Hello", target_lang="English"))
        _assert_valid_audio_stream(chunks)

    def test_streams_with_custom_voice(self):
        """Custom voice description still produces a valid audio stream."""
        chunks = list(tts("Hello", target_lang="English", voice="A deep male narrator voice"))
        _assert_valid_audio_stream(chunks)

    def test_streams_with_empty_voice(self):
        """Empty voice string still produces a valid audio stream."""
        chunks = list(tts("Hello", target_lang="English", voice=""))
        _assert_valid_audio_stream(chunks)
