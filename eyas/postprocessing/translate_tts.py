"""Translation and TTS helper wrappers.

Wrap translation APIs or local models and a TTS backend.
"""


def translate(text: str, target_lang: str = "en") -> str:
    # TODO: call Cohere or local translation model
    return text


def tts(text: str, voice: str = "default") -> bytes:
    # TODO: call local VoxCPM2 or external TTS and return audio bytes
    return b""
