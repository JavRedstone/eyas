# input

Sample and test input files used during development.

## Files

| File | Description |
|---|---|
| `sample.mp4` | Short retail-scene clip used for manual pipeline runs |
| `events.json` | Last event log written by the pipeline (overwritten on each run) |

## Note

`events.json` is regenerated every time `run_visual_pipeline.py` or `test_module_tracker_structurer.py` completes. The canonical fixture copy lives in `tests/samples/events.json`.
