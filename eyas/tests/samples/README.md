# tests/samples

Fixture files used by module and e2e tests.

## Files

| File | Description |
|---|---|
| `sample.mp4` | Short retail-scene video clip (~3 MB). Used as the default input for all video-based tests. |
| `events.json` | Event log written by `test_module_tracker_structurer.py`. Consumed by `test_reasoning_integration.py`. Regenerated on each tracker-structurer test run. |

## Note

Do not delete `sample.mp4` — it is the only video fixture. If you replace it, ensure it contains at least one visible person so that YOLO tracking tests can assert `len(seen_ids) > 0`.
