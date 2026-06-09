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
from eyas.postprocessing.translate_tts import translate, tts


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
                    "role": "user",
                    "content": "Translate the following text to Korean: hello",
                }
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
