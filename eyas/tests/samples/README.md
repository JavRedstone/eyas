# tests/samples

Fixture files used by module and e2e tests.

## Files

| File | Description |
|---|---|
| `sample.mp4` | Short retail-scene video clip (~3 MB). Used as the default input for all video-based tests. |
| `events.json` | Event log written by `test_module_tracker_structurer.py`. Consumed by `test_reasoning_integration.py`. Regenerated on each tracker-structurer test run. |

## Sample event schema

A representative event entry (pickup confirmed, no items identified):

```json
{
  "track_id": 2,
  "timestamp": 5.84,
  "confirmation_timestamp": 5.84,
  "description": "Two individuals in a convenience store, one in dark clothing bending over a shelf, the other standing with hands on hips. Shelves with products are visible, and decorative snowflakes hang above. The floor has a tiled pattern with square accents.",
  "activity": "The person in dark clothing bends down to interact with a shelf, possibly picking up or examining an item, while the standing person observes. The standing person then stands still, with hands on hips, indicating no active interaction.",
  "held_objects": [],
  "pickup_confirmed": true,
  "picked_up_items": [],
  "summary": "Two individuals in a convenience store, one in dark clothing bending over a shelf...",
  "zone": "counter",
  "backend": "minicpmv",
  "bbox": [1182, 235, 1476, 912],
  "confidence": 0.857,
  "source_video": "20260608_130000_counter.mp4",
  "source_clip_id": "20260614_121209",
  "source_event_index": 5
}
```

Key fields:
- `pickup_confirmed: true` with `picked_up_items: []` — the unidentified-item path; structurer seeds a placeholder, reasoner emits `"YES (item unidentified)"`
- `raw_observation` — raw VLM JSON before heuristic overrides (note `pickup_confirmed: false` in raw vs `true` in structured output)
- `source_video` / `source_clip_id` / `source_event_index` — traceability back to the original video and session

## Note

Do not delete `sample.mp4` — it is the only video fixture. If you replace it, ensure it contains at least one visible person so that YOLO tracking tests can assert `len(seen_ids) > 0`.
