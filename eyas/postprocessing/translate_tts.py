"""Translation and TTS helper wrappers.

Wrap translation APIs or local models and a TTS backend.
"""

from collections.abc import Iterator
import sys
from pathlib import Path

import numpy as np

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from eyas.postprocessing import (
    TINYAYA_SUPPORTED_LANGUAGES,
    TTS_SAMPLE_RATE,
    VOXCPM2_MODEL,
    VOXCPM2_SUPPORTED_LANGUAGES,
    get_tinyaya_model,
)


def translate(text: str, target_lang: str = "English") -> str:
    # https://huggingface.co/CohereLabs/tiny-aya-global-GGUF
    if target_lang not in TINYAYA_SUPPORTED_LANGUAGES:
        raise ValueError(f"Target language {target_lang} not supported")

    response = get_tinyaya_model().create_chat_completion(
        messages=[
            {
                "role": "user",
                "content": f"Translate the following text to {target_lang}: {text}",
            }
        ],
        max_tokens=4096,
        temperature=0.1,
        top_p=0.95,
    )
    return response["choices"][0]["message"]["content"].strip()


def tts(text: str, target_lang: str = "English", voice: str = "A young woman, gentle and sweet voice") -> Iterator[tuple[int, np.ndarray]]:
    # https://huggingface.co/openbmb/VoxCPM2

    if target_lang not in VOXCPM2_SUPPORTED_LANGUAGES:
        raise ValueError(f"Target language {target_lang} not supported")

    if not text.strip():
        raise ValueError("Text is empty")

    if voice:
        text = f"({voice}){text}"

    for chunk in VOXCPM2_MODEL.generate_streaming(text=text):
        yield TTS_SAMPLE_RATE, chunk.astype(np.float32)

if __name__ == "__main__":
    print(translate("Hello, how are you?", target_lang="Korean"))
    for chunk in tts("Hello, how are you?", target_lang="Korean"):
        print(chunk)