# event_structuring

Converts per-frame YOLO tracks + VLM observations into a timestamped, zone-aware event log.

## Key exports

| Symbol | Description |
|---|---|
| `EventStructurer` | Main orchestrator — call `update(tracks, t, latest_frame)` each frame |
| `Zone` | Named spatial region with a bounding box and kind (`"shelf"`, `"exit"`, …) |
| `Event` | Output dataclass — `track_id`, `timestamp`, `zone`, `summary`, `pickup_confirmed`, … |
| `build_events(detections, annotations)` | Lower-level helper to build events from raw dicts |

## How it works

1. Each tracked person is assigned to the zone(s) they overlap.
2. Every `semantic_interval_s` seconds the VLM is invoked on recent crop history.
3. If `"reaching"` activity is followed by a new `held_object`, a pickup is inferred and the earlier event is back-patched with `pickup_confirmed=True`.
4. `to_json(path)` serialises all events for downstream LLM reasoning.

## Usage

```python
from event_structuring.structurer import EventStructurer, Zone

zones = [Zone("shelf_A", bbox=(0, 0, 640, 480), kind="shelf")]
structurer = EventStructurer(zones, vlm=vlm, semantic_interval_s=2.0)

for frame in video:
    tracks = tracker.track(frame)
    events = structurer.update(tracks, timestamp, latest_frame=frame)

structurer.to_json("output/events.json")
```
