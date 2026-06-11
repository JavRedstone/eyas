"""Model tests for the TinyAya translation model.

Requires llama-cpp-python and HuggingFace model access.

Run:
    pytest eyas/tests/model/test_translation.py -v -s
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import pytest

pytest.importorskip("llama_cpp")

from eyas.postprocessing.translate_tts import translate

_W = 72

LONG_ALERT = (
    "Suspicious activity detected at shelf A. "
    "Person loitering near the back door for over three minutes. "
    "Confidence score 0.91 at 02:14 AM."
)


def _box(title: str, body: str) -> None:
    print(f"\n{'=' * _W}")
    print(f"  {title}")
    print(f"{'-' * _W}")
    for line in str(body).splitlines():
        print(f"  {line}")
    print(f"{'=' * _W}")


class TestTranslate:
    def test_translate_to_korean_changes_output(self):
        source = "Hello, how are you?"
        result = translate(source, target_lang="Korean")
        _box("translate → Korean", f"source : {source}\nresult : {result}")

        assert result
        assert result.strip() != source
        assert "Translate the following" not in result

    def test_translate_default_english(self):
        source = "Bonjour, comment allez-vous?"
        result = translate(source)
        _box("translate → English (default)", f"source : {source}\nresult : {result}")

        assert result
        assert isinstance(result, str)

    def test_accepts_supported_target_lang(self):
        source = "hello"
        result = translate(source, target_lang="Korean")
        _box("translate → Korean (short)", f"source : {source}\nresult : {result}")

        assert result
        assert isinstance(result, str)

    def test_translate_use_gpu_false(self):
        source = "hello"
        result = translate(source, target_lang="Korean", use_gpu=False)
        _box("translate → Korean (use_gpu=False)", f"source : {source}\nresult : {result}")

        assert result
        assert isinstance(result, str)

    def test_translate_long_alert_text(self):
        result = translate(LONG_ALERT, target_lang="English")
        _box("translate alert → English", f"source : {LONG_ALERT}\nresult : {result}")

        assert result
        assert "Translate the following" not in result


class TestTranslateLanguageCoverage:
    def test_welsh_supported(self):
        source = "hello"
        result = translate(source, target_lang="Welsh")
        _box("translate → Welsh", f"source : {source}\nresult : {result}")

        assert result
        assert isinstance(result, str)

    def test_rejects_unsupported_language(self):
        with pytest.raises(ValueError, match="Klingon"):
            translate("hello", target_lang="Klingon")


if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
