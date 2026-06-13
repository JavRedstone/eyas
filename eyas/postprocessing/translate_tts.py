"""Translation and TTS helper wrappers.

Wrap translation APIs or local models and a TTS backend.
"""

# TODO: smaller max_tokens once we see the output length 
# TODO: warm up models once at startup during app initialization

from collections.abc import Iterator
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
import numpy as np
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import os

from eyas.postprocessing import (
    TINYAYA_SUPPORTED_LANGUAGES,
    VOXCPM2_SUPPORTED_LANGUAGES,
    get_tinyaya_model,
    get_voxcpm2_model,
    get_voxcpm2_model_nano,
    VOXCPM2_NANO_SAMPLE_RATE,
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
_tinyaya_lock = threading.Lock()


def clear_translation_cache() -> None:
    """Clear the in-memory translation cache (for tests)."""
    _translation_cache.clear()


_SYSTEM_PROMPT = (
    "You are a translation engine. "
    "Output only the translated text. "
    "No explanations, notes, or language detection."
)

_META_PHRASES = (
    "이 문장은",
    "already written in",
    "영어로 번역",
    "If translated to",
    "Translate the following",
    "다음과 같이",
)


def _translation_messages(text: str, target_lang: str, *, strict: bool = False) -> list[dict[str, str]]:
    if strict:
        user_content = (
            f"Translate to {target_lang}. Reply with ONLY the translation, nothing else:\n{text}"
        )
    else:
        user_content = f"Translate to {target_lang}:\n{text}"
    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def _looks_like_meta_response(_source: str, result: str) -> bool:
    if not result:
        return True
    lower = result.lower()
    for phrase in _META_PHRASES:
        if phrase.lower() in lower:
            return True
    return False


def _call_translation_model(
    text: str,
    target_lang: str,
    *,
    strict: bool,
    use_gpu: bool,
) -> str:
    with _tinyaya_lock:
        response = get_tinyaya_model(use_gpu=use_gpu).create_chat_completion(
            messages=_translation_messages(text, target_lang, strict=strict),
            max_tokens=4096,
            temperature=0,
            top_p=0.95,
        )
    return response["choices"][0]["message"]["content"].strip()


def _is_cacheable(source: str, result: str) -> bool:
    """Cache only clean translations — not meta garbage or source fallbacks."""
    if _looks_like_meta_response(source, result):
        return False
    return result != source


def translate(text: str, target_lang: str = "English", use_gpu: bool = True) -> str:
    # https://huggingface.co/CohereLabs/tiny-aya-global-GGUF
    if target_lang not in TINYAYA_SUPPORTED_LANGUAGES:
        raise ValueError(f"Target language {target_lang} not supported")

    stripped = text.strip()
    result = _call_translation_model(stripped, target_lang, strict=False, use_gpu=use_gpu)
    if not _looks_like_meta_response(stripped, result):
        return result

    retry = _call_translation_model(stripped, target_lang, strict=True, use_gpu=use_gpu)
    if not _looks_like_meta_response(stripped, retry):
        return retry

    return stripped


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
    if _is_cacheable(stripped, result):
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


def _use_nanovllm() -> bool:
    """True on bare CUDA (dedicated GPU). False on ZeroGPU, MPS, or CPU.

    nanovllm starts persistent worker processes that hold a GPU reference.
    ZeroGPU only provides GPU access inside @spaces.GPU windows, so the workers
    would lose the device after the first call returns.
    """
    zero_gpu = os.getenv("EYAS_ZERO_GPU", "").strip().lower() in {"1", "true", "yes", "on"}
    if zero_gpu:
        return False
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


def tts(text: str, target_lang: str = "English", voice: str = "A young woman, gentle and sweet voice") -> Iterator[tuple[int, np.ndarray]]:
    # https://huggingface.co/openbmb/VoxCPM2

    if target_lang not in VOXCPM2_SUPPORTED_LANGUAGES:
        raise ValueError(f"Target language {target_lang} not supported")

    if not text.strip():
        raise ValueError("Text is empty")

    if voice:
        text = f"({voice}){text}"

    if _use_nanovllm():
        try:
            server = get_voxcpm2_model_nano()
            for chunk in server.generate(target_text=text):
                yield VOXCPM2_NANO_SAMPLE_RATE, chunk.astype(np.float32)
            return
        except RuntimeError:
            pass  # nano-vllm-voxcpm not installed; fall through to standard backend

    model, sample_rate = get_voxcpm2_model()
    for chunk in model.generate_streaming(text=text):
        yield sample_rate, chunk.astype(np.float32)