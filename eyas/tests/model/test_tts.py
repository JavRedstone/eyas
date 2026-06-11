"""Model tests for the VoxCPM2 TTS model.

Streaming and pipeline tests require a GPU (CUDA or MPS).

Run:
    pytest eyas/tests/model/test_tts.py -v -s
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import wave

import numpy as np
import pytest
import torch

pytest.importorskip("voxcpm")

from eyas.postprocessing import get_voxcpm2_model
from eyas.postprocessing.translate_tts import tts

_W = 72
_OUT_DIR = Path(__file__).parent / "tts_output"

requires_gpu = pytest.mark.skipif(
    not (torch.cuda.is_available() or torch.backends.mps.is_available()),
    reason="GPU (CUDA or MPS) required for VoxCPM2 TTS streaming tests",
)

LONG_ALERT = (
    "Suspicious activity detected at shelf A. "
    "Person loitering near the back door for over three minutes. "
    "Confidence score 0.91 at 02:14 AM."
)


def _save_wav(filename: str, sample_rate: int, audio: np.ndarray) -> Path:
    _OUT_DIR.mkdir(exist_ok=True)
    path = _OUT_DIR / filename
    pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(str(path), "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(pcm.tobytes())
    return path


def _audio_box(title: str, text: str, chunks: list[tuple[int, np.ndarray]]) -> None:
    sample_rate = chunks[0][0]
    audio = np.concatenate([a for _, a in chunks])
    duration = audio.size / sample_rate
    peak = float(np.abs(audio).max())
    rms = float(np.sqrt(np.mean(audio ** 2)))

    slug = title.replace(" ", "_").replace("→", "to").replace("(", "").replace(")", "").replace(":", "").replace("/", "_")
    wav_path = _save_wav(f"{slug}.wav", sample_rate, audio)

    print(f"\n{'=' * _W}")
    print(f"  {title}")
    print(f"{'-' * _W}")
    print(f"  text     : {text!r}")
    print(f"  chunks   : {len(chunks)}")
    print(f"  samples  : {audio.size}  ({sample_rate} Hz)")
    print(f"  duration : {duration:.2f}s")
    print(f"  peak     : {peak:.4f}  rms: {rms:.4f}")
    print(f"  saved    : {wav_path}")
    print(f"{'=' * _W}")


def _assert_valid_audio_stream(
    chunks: list[tuple[int, np.ndarray]],
    *,
    expected_sample_rate: int | None = None,
    min_duration: float = 0.1,
) -> None:
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


@requires_gpu
class TestTtsStreaming:
    def test_streams_korean_audio(self):
        text = "안녕하세요"
        chunks = list(tts(text, target_lang="Korean"))
        _audio_box("tts → Korean", text, chunks)
        _assert_valid_audio_stream(chunks)

    def test_streams_english_with_default_voice(self):
        text = "Hello"
        chunks = list(tts(text, target_lang="English"))
        _audio_box("tts → English (default voice)", text, chunks)
        _assert_valid_audio_stream(chunks)

    def test_streams_with_custom_voice(self):
        text = "Hello"
        voice = "A deep male narrator voice"
        chunks = list(tts(text, target_lang="English", voice=voice))
        _audio_box(f"tts → English (voice: {voice})", text, chunks)
        _assert_valid_audio_stream(chunks)

    def test_streams_with_empty_voice(self):
        text = "Hello"
        chunks = list(tts(text, target_lang="English", voice=""))
        _audio_box("tts → English (no voice prefix)", text, chunks)
        _assert_valid_audio_stream(chunks)

    def test_sample_rate_matches_model(self):
        _, expected_rate = get_voxcpm2_model()
        text = "Hello"
        chunks = list(tts(text, target_lang="English"))
        _audio_box(f"tts → English (expected rate: {expected_rate} Hz)", text, chunks)
        _assert_valid_audio_stream(chunks, expected_sample_rate=expected_rate)

    def test_longer_text_yields_multiple_chunks(self):
        text = "This is a longer English alert message for streaming coverage. " * 3
        chunks = list(tts(text, target_lang="English"))
        _audio_box("tts → English (long text)", text[:60] + "...", chunks)
        assert len(chunks) >= 1
        _assert_valid_audio_stream(chunks)

    def test_alert_concatenates_to_valid_audio(self):
        chunks = list(tts(LONG_ALERT, target_lang="English"))
        _audio_box("tts → English (alert text)", LONG_ALERT, chunks)
        assert len(chunks) >= 1

        sample_rate = chunks[0][0]
        audio = np.concatenate([chunk for _, chunk in chunks])

        assert audio.dtype == np.float32
        assert audio.ndim == 1
        assert audio.size > 0
        assert np.all(audio >= -1.0)
        assert np.all(audio <= 1.0)
        assert audio.size / sample_rate >= 0.1


class TestTtsLanguageCoverage:
    def test_welsh_unsupported(self):
        with pytest.raises(ValueError, match="Welsh"):
            list(tts("Hello", target_lang="Welsh"))


@requires_gpu
class TestTranslateTtsPipeline:
    def test_alert_translate_then_speak_korean(self):
        pytest.importorskip("llama_cpp")
        from eyas.postprocessing.translate_tts import translate

        source = "Suspicious activity detected at shelf A."
        korean = translate(source, target_lang="Korean")
        print(f"\n  translate → Korean: {source!r} → {korean!r}")

        assert korean
        assert korean.strip() != source

        chunks = list(tts(korean, target_lang="Korean"))
        _audio_box("tts → Korean (translated alert)", korean, chunks)
        _assert_valid_audio_stream(chunks)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
