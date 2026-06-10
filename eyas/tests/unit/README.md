# tests/unit

Fast, dependency-free unit tests. No video files, no model weights, no GPU needed.

## Coverage

| Test file | Module under test |
|---|---|
| `test_object_detection.py` | `Track` dataclass, `crop()` function, `detect_objects()` |
| `test_observation_parsing.py` | `parse_person_observation()`, `PERSON_STATUS_PROMPT` |
| `test_event_structuring.py` | `build_events()`, `EventStructurer` pickup inference, evidence crops |
| `test_llm_prompts.py` | Prompt templates and GBNF grammar strings |
| `test_llm_reasoner.py` | `Reasoner` methods with mocked `llama_cpp` |
| `test_streaming.py` | `StreamCapture` lifecycle with mocked `cv2` |
| `test_storage.py` | Clip storage manager with `tmp_path` isolation |
| `test_video_processing.py` | `process_clip()` return-type contract |
| `test_translate_tts.py` | `translate()` / `tts()` — mocked validation, strict prompt, meta retry/fallback, cache guard (no GPU) |
| `test_locale.py` | `ui/locale.py` — en/ko catalogs, table headers, `format_event_row()`, display helpers |
| `test_overlay_text.py` | `utils/overlay_text.py` — localized label strings, Pillow text draw smoke test |

## Run

```bash
pytest tests/unit/ -v
```
