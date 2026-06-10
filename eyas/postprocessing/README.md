# postprocessing

Translation and text-to-speech for operator alerts.

## Key exports

| Symbol | Description |
|---|---|
| `translate(text, target_lang)` | Translate `text` to `target_lang` using TinyAya (llama.cpp); validates output and retries once on meta/explanation garbage |
| `translate_cached(text, target_lang)` | Cached wrapper; only stores clean translations (not fallbacks or invalid output) |
| `tts(text, target_lang, voice)` | Stream `(sample_rate, audio_chunk)` tuples via VoxCPM2 (requires CUDA) |

## Translation behavior

When `translate()` gets an invalid response (known meta phrases such as language-detection notes), it retries with a stricter prompt. If the retry is still invalid, it returns the original source text unchanged.

## Dependencies

| Feature | Requirement |
|---|---|
| Translation | `llama-cpp-python` + a GGUF model |
| TTS | `voxcpm` + CUDA GPU |

Both are optional — the rest of the pipeline runs without them.

## Usage

```python
from postprocessing.translate_tts import translate, tts

korean = translate("Suspicious activity detected at shelf A.", target_lang="Korean")
for sample_rate, audio in tts(korean, target_lang="Korean"):
    play(sample_rate, audio)
```
