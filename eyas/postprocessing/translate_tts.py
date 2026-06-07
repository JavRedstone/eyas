"""Translation and TTS helper wrappers.

Wrap translation APIs or local models and a TTS backend.
"""

from collections.abc import Iterator

import numpy as np

from . import (
    TINYAYA_GLOBAL_MODEL,
    TINYAYA_GLOBAL_TOKENIZER,
    TINYAYA_SUPPORTED_LANGUAGES,
    TTS_SAMPLE_RATE,
    VOXCPM2_MODEL,
    VOXCPM2_SUPPORTED_LANGUAGES,
)


def translate(text: str, target_lang: str = "English") -> str:
    # https://huggingface.co/CohereLabs/tiny-aya-global
    if target_lang not in TINYAYA_SUPPORTED_LANGUAGES:
        raise ValueError(f"Target language {target_lang} not supported")

    messages = [{"role": "user", "content": f"Translate the following text to {target_lang}: {text}"}]
    input_ids = TINYAYA_GLOBAL_TOKENIZER.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt",
    ).to(TINYAYA_GLOBAL_MODEL.device)

    gen_tokens = TINYAYA_GLOBAL_MODEL.generate(
        input_ids,
        max_new_tokens=4096,
        do_sample=True,
        temperature=0.1,
        top_p=0.95,
    )

    new_tokens = gen_tokens[0][input_ids.shape[-1] :]
    return TINYAYA_GLOBAL_TOKENIZER.decode(new_tokens, skip_special_tokens=True)


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
