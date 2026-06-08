# tests

Three-layer test suite. Run from the `eyas/` directory.

## Layers

| Folder | Speed | Models needed | Command |
|---|---|---|---|
| `unit/` | Fast (< 5 s) | None | `pytest tests/unit/` |
| `module/` | Slow (needs video + optional GPU) | YOLO, optionally MiniCPM-V / GGUF | `pytest tests/module/` |
| `e2e/` | Slowest (full stack) | MiniCPM-V + GGUF | `pytest tests/e2e/` |

Tests in `module/` and `e2e/` that require unavailable models are automatically skipped.

## Shared fixtures

`conftest.py` at this level provides:
- `get_device()` — returns `"cuda"` / `"mps"` / `"cpu"` (imported from `utils.device`)
- `device` — session-scoped pytest fixture wrapping `get_device()`

## Sample data

`samples/` holds the fixtures used by module and e2e tests:
- `sample.mp4` — short retail-scene clip
- `events.json` — event log produced by the module tracker test

## Running all tests

```bash
pytest tests/ -v
```
