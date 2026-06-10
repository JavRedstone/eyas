"""Translation and TTS helper wrappers.

Wrap translation APIs or local models and a TTS backend.
"""

# TODO: smaller max_tokens once we see the output length 
# TODO: warm up models once at startup during app initialization

from collections.abc import Iterator
import sys
import time
from dataclasses import dataclass
from pathlib import Path
import numpy as np
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from eyas.postprocessing import (
    TINYAYA_SUPPORTED_LANGUAGES,
    VOXCPM2_SUPPORTED_LANGUAGES,
    get_tinyaya_model,
    get_voxcpm2_model,
)


@dataclass
class TranslateStats:
    """Timing and cache stats for a translation batch or single call."""

    elapsed_s: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0

    def merge(self, other: "TranslateStats") -> "TranslateStats":
        return TranslateStats(
            elapsed_s=self.elapsed_s + other.elapsed_s,
            cache_hits=self.cache_hits + other.cache_hits,
            cache_misses=self.cache_misses + other.cache_misses,
        )


_translation_cache: dict[tuple[str, str], str] = {}


def clear_translation_cache() -> None:
    """Clear the in-memory translation cache (for tests)."""
    _translation_cache.clear()


def translate(text: str, target_lang: str = "English", use_gpu: bool = True) -> str:
    # https://huggingface.co/CohereLabs/tiny-aya-global-GGUF
    if target_lang not in TINYAYA_SUPPORTED_LANGUAGES:
        raise ValueError(f"Target language {target_lang} not supported")

    response = get_tinyaya_model(use_gpu=use_gpu).create_chat_completion(
        messages=[
            {
                "role": "user",
                "content": f"Translate the following text to {target_lang}: {text}",
            }
        ],
        max_tokens=4096, # max number of tokens in the output
        temperature=0, # take the most likely output
        top_p=0.95,
    )
    return response["choices"][0]["message"]["content"].strip()


def translate_cached(
    text: str,
    target_lang: str = "English",
    use_gpu: bool = True,
) -> tuple[str, TranslateStats]:
    """Translate with in-memory cache; returns (result, stats)."""
    stripped = text.strip()
    if not stripped:
        return text, TranslateStats()

    key = (stripped, target_lang)
    if key in _translation_cache:
        return _translation_cache[key], TranslateStats(cache_hits=1)

    start = time.perf_counter()
    result = translate(stripped, target_lang=target_lang, use_gpu=use_gpu)
    elapsed = time.perf_counter() - start
    _translation_cache[key] = result
    return result, TranslateStats(elapsed_s=elapsed, cache_misses=1)


def translate_many(
    texts: set[str],
    target_lang: str,
    use_gpu: bool = True,
) -> tuple[dict[str, str], TranslateStats]:
    """Translate a set of strings, deduplicated via cache."""
    mapping: dict[str, str] = {}
    stats = TranslateStats()
    for text in texts:
        if not text or not text.strip():
            continue
        translated, item_stats = translate_cached(text, target_lang, use_gpu=use_gpu)
        mapping[text] = translated
        stats = stats.merge(item_stats)
    return mapping, stats


def tts(text: str, target_lang: str = "English", voice: str = "A young woman, gentle and sweet voice") -> Iterator[tuple[int, np.ndarray]]:
    # https://huggingface.co/openbmb/VoxCPM2

    if target_lang not in VOXCPM2_SUPPORTED_LANGUAGES:
        raise ValueError(f"Target language {target_lang} not supported")

    if not text.strip():
        raise ValueError("Text is empty")

    if voice:
        text = f"({voice}){text}"

    model, sample_rate = get_voxcpm2_model()
    for chunk in model.generate_streaming(text=text):
        yield sample_rate, chunk.astype(np.float32)