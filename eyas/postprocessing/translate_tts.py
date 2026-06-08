"""Translation and TTS helper wrappers.

Wrap translation APIs or local models and a TTS backend.
"""

# TODO: smaller max_tokens once we see the output length 
# TODO: warm up models once at startup during app initialization

from collections.abc import Iterator
import sys
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