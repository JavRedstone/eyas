# tests

Three-layer test suite. Run all commands from the repo root.

## Layers

| Folder | Speed | Models needed |
|---|---|---|
| `unit/` | Fast (< 5 s) | None |
| `model/` | Slow (needs video + optional GPU) | YOLO, optionally MiniCPM-V / GGUF / TinyAya / VoxCPM2 |
| `e2e/` | Slowest (full stack) | MiniCPM-V + GGUF |

Tests in `model/` and `e2e/` that require unavailable models are automatically skipped.

## Running tests

```bash
# All layers
pytest eyas/tests/ -v

# One layer
pytest eyas/tests/unit/
pytest eyas/tests/model/
pytest eyas/tests/e2e/

# One file
pytest eyas/tests/model/test_tts.py -v -s
pytest eyas/tests/unit/test_llm_reasoner.py -v

# One test class
pytest eyas/tests/model/test_tts.py::TestTtsStreaming -v -s

# One specific test
pytest eyas/tests/model/test_tts.py::TestTtsStreaming::test_streams_english_with_default_voice -v -s

# By keyword (matches test name, class name, or file name)
pytest eyas/tests/ -k "translate" -v
pytest eyas/tests/ -k "tts and not pipeline" -v
```

## Useful flags

| Flag | Effect |
|---|---|
| `-v` | Show each test name as it runs |
| `-s` | Print model output (don't capture stdout) — use for model tests |
| `-v -s` | Both — recommended for `model/` tests |
| `--tb=short` | Shorter traceback on failure (default is `long`) |
| `-x` | Stop after first failure |
| `-k "<expr>"` | Run only tests whose name matches the expression |

## Environment variables

| Variable | Default | Used by |
|---|---|---|
| `EYAS_MODEL_PATH` | `eyas/models/nemotron-nano-4b.gguf` | `test_reasoning_integration.py` |
| `EYAS_GPU_LAYERS` | `-1` (all layers on GPU) | `test_reasoning_integration.py` |
| `EYAS_TINYAYA_GGUF_FILE` | `tiny-aya-global-q4_k_m.gguf` | `test_translation.py` |
| `EYAS_TINYAYA_N_CTX` | `4096` | `test_translation.py` |

```bash
# Example: override model path and run only reasoning tests with output
EYAS_MODEL_PATH=eyas/models/mymodel.gguf pytest eyas/tests/model/test_reasoning_integration.py -v -s
```

## TTS audio output

`test_tts.py` saves a WAV file per test to `eyas/tests/model/tts_output/` (gitignored).
Open any file with QuickTime or `open eyas/tests/model/tts_output/` to hear the model output.

## Shared fixtures

`conftest.py` at this level provides:
- `device` — session-scoped fixture returning `"cuda"` / `"mps"` / `"cpu"`

## Sample data

`samples/` holds fixtures used by `model/` and `e2e/` tests:
- `sample.mp4` — short retail-scene clip
- `events.json` — event log produced by the model tracker test
