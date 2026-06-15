# TinyAya Global — Korean Translator

**Role in pipeline:** Postprocessing — localization layer  
**HF model:** [CohereLabs/tiny-aya-global-GGUF](https://huggingface.co/CohereLabs/tiny-aya-global-GGUF)  
**File:** `tiny-aya-global-q4_k_m.gguf`  
**Size:** ~0.5 GB (Q4_K_M quantized)  
**Runtime:** llama-cpp-python (CPU / CUDA)  
**Sponsor:** [Cohere](https://cohere.com/)

---

## What it does

TinyAya translates free-text fields in Eyas from English to Korean (or other supported locales). It runs after the visual pipeline completes and handles the parts of the output that can't be covered by a static string table:

- VLM-generated `activity` text (e.g., "bends down and interacts with a shelf item")
- VLM-generated `description` text (scene descriptions)
- LLM-generated `summary` narrative
- Q&A replies from the LLM
- TTS input (spoken Korean security brief)

Static labels (zone names, event kind chips, UI strings) use the frontend `i18n.js` catalog and don't go through TinyAya.

## Supported languages

TinyAya Global covers a wide range of languages organized by region. For Eyas, Korean (`ko`) is the primary target, but the same translation path works for any language TinyAya supports by passing a different `locale` argument.

## Runtime

```python
Llama.from_pretrained(
    repo_id="CohereLabs/tiny-aya-global-GGUF",
    filename="tiny-aya-global-q4_k_m.gguf",
    n_gpu_layers=-1,   # GPU if available
)
```

Translation calls are **cached** — the same source string in the same locale is only translated once per session. Calls also include a single retry if the model returns the source string unchanged (a common failure mode for very short inputs).

## Hot-swap at runtime

When the operator switches from English to Korean in the UI header:

1. The frontend calls `/save_language` to persist the preference
2. `refreshLocalization` is called with the full session snapshot (events, summary, chat history, per-clip queue summaries)
3. Parallel `predict('/localize_events')`, `predict('/localize_summary')`, and `predict('/localize_chat')` calls fire
4. TinyAya translates all free-text fields in parallel tasks
5. The results are merged back into React state

This means switching languages doesn't require re-running the pipeline — all previously generated text is translated on the fly.

## Challenges

### Two-tier translation architecture

The hardest design problem with localization was that not everything needs TinyAya, and calling TinyAya for everything is slow. Eyas has two categories of text that need Korean:

1. **Static strings** — tab labels, button text, column headers, risk level names, event kind chips, zone names. These are finite, known in advance, and always the same. TinyAya would be wasteful here.
2. **Freeform VLM/LLM text** — the `activity` field, scene `description`, LLM `summary` narrative, Q&A replies. These are unique per observation and can't be pre-translated.

The architecture splits cleanly: static strings live in `i18n.js` (frontend) and `locale.py` (backend), and are just hardcoded Korean equivalents. Freeform text goes through TinyAya at runtime. Getting this boundary right required auditing every string in the UI and pipeline output to decide which category it belonged to.

The tricky edge cases were zone names and event kind labels — both appear to be "static" (e.g., "counter", "pickup") but the actual zone string in an event comes from the VLM's free-text output and may not exactly match the static table. The resolution: zone names are normalized to known identifiers during event structuring, so they can be looked up in the static table; if the normalization fails, TinyAya translates the raw string.

### TinyAya returning the source string unchanged

For short inputs — especially single words or technical terms — TinyAya would sometimes return the exact input string as the "translation". This is a known failure mode of small translation models: they have no confidence and reproduce the input. The fix was a single retry with a more explicit prompt if the output equals the input, and caching both the success and the known-bad result to avoid repeated retries.

### Activity field initially missed

The `activity` field on each event was the last to get Korean translation. The description and zone fields were wired up first; `activity` was overlooked in the initial `localize_events_for_display()` implementation and appeared in English even when the rest of the event was in Korean. This was caught during store testing when the activity column stayed English while everything else switched.

## Why this model

- **Size** — ~0.5 GB is small enough to load alongside Nemotron without memory pressure.
- **Multilingual coverage** — TinyAya Global is trained on the Aya dataset, Cohere's massively multilingual instruction corpus covering 100+ languages. Translation quality for Korean is good for short event-style sentences.
- **No API** — same as the other models: runs on-device, no external calls.
- **Sponsor** — Cohere is a Build Small Hackathon sponsor.

## Where it lives in the code

| File | Role |
|------|------|
| [eyas/postprocessing/\_\_init\_\_.py](../../eyas/postprocessing/__init__.py) | `get_tinyaya_model()`, `TINYAYA_GGUF_REPO`, cache dict, translation helper |
| [eyas/ui/locale.py](../../eyas/ui/locale.py) | `localize_events_for_display()` — calls TinyAya for `activity`, `description`, `zone`; also exposes Gradio endpoints `/localize_events`, `/localize_summary`, `/localize_chat`, `/localize_zones` |
| [eyas/ui/frontend/src/App.jsx](../../eyas/ui/frontend/src/App.jsx) | `refreshLocalization()` — orchestrates the parallel localization calls on language switch |
