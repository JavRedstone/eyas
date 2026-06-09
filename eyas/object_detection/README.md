# object_detection

YOLO11 + BotSORT person detection and tracking.

## Key exports

| Symbol | Description |
|---|---|
| `PersonTracker` | Wraps Ultralytics YOLO with BotSORT; returns `Track` objects per frame |
| `Track` | Dataclass — `track_id`, `label`, `confidence`, `bbox (x1,y1,x2,y2)` |
| `crop(frame, bbox, pad)` | Extract a region from a BGR frame with clamped padding |
| `detect_objects(frame)` | One-shot detection without tracking (lazy default tracker) |

## Model

Default weights: `models/yolo11n.pt` (resolved via `utils.paths.models_dir()`).  
Swap weights by passing `weights=` to `PersonTracker`.

## Usage

```python
from object_detection.detector import PersonTracker, crop

tracker = PersonTracker(conf=0.4, device="cuda")
tracks = tracker.track(frame)          # list[Track]
person_img = crop(frame, tracks[0].bbox, pad=20)
```
