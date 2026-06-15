# YOLO11n + BotSORT — Person Tracker

**Role in pipeline:** Stage 1 — spatial detection layer  
**HF / source:** [ultralytics/assets](https://github.com/ultralytics/assets) (auto-downloaded as `eyas/models/yolo11n.pt`)  
**Size:** ~6 MB  
**Runtime:** PyTorch (CPU / MPS / CUDA)

---

## What it does

YOLO11n is the fastest model in Ultralytics' YOLOv11 family. In Eyas it acts as the "fast spatial layer" — running on every frame to find and lock onto people before the slower VLM ever fires.

It is paired with **BotSORT**, a Re-ID-aware tracker that assigns consistent integer track IDs across frames. A person who briefly disappears behind a shelf gets the same ID when they reappear, so the event structurer can follow a single person's behavior across an extended observation window rather than treating each re-entry as a new subject.

## What it does NOT do

YOLO11n is trained on COCO-80 and cannot recognize branded retail products (chips, drinks, etc.). Asking it to detect "a can of Coke" would fail. That's intentional: YOLO's only job is to answer "is there a person here, and where are they?" Product recognition belongs to the VLM.

## Output

```python
@dataclass
class Track:
    track_id:   int
    label:      str          # always "person" in Eyas
    confidence: float
    bbox:       Tuple[int, int, int, int]  # x1, y1, x2, y2
```

Each track also carries a padded crop of the bounding box. Those crops are buffered and fed to MiniCPM-V for visual analysis.

## Configuration

```python
PersonTracker(
    weights = "eyas/models/yolo11n.pt",  # nano — fastest, ~6 MB
    tracker = "botsort.yaml",            # Re-ID: survives occlusion, best for store footage
    conf    = 0.6,                       # confidence threshold
    classes = [0],                       # COCO class 0 = person only
)
```

Tracker alternatives:
- `bytetrack.yaml` — lighter, no Re-ID (use if BotSORT is too slow)
- `botsort.yaml` (default) — Re-ID enabled, better identity continuity across partial occlusions

## Why this model

- **Size** — 6 MB means it loads in milliseconds and leaves room for the larger VLM and LLM.
- **Speed** — nano inference at ~10–30 ms/frame on CPU; leaves budget for VLM and event logic.
- **Person accuracy** — COCO's "person" class is the most heavily represented; nano still hits >50% mAP on it.
- **BotSORT Re-ID** — convenience store footage is full of occlusions (shelves, other customers). Re-ID keeps track IDs stable and lets the event buffer accumulate a meaningful observation window.

## Challenges

### Track ID instability across occlusions

The biggest problem with a retail store environment is constant occlusion — customers block each other behind shelves, step behind pillars, or briefly leave the camera frame. Without Re-ID, every re-entry spawns a new track ID, which breaks the event structurer's per-track observation buffer. A person who ducks behind a shelf and re-emerges two seconds later would be treated as a completely new subject, resetting the evidence window and losing the history needed to confirm a pickup.

BotSORT's appearance-based Re-ID reduces this significantly, but doesn't eliminate it entirely. Long occlusions (>3–4 seconds) still cause ID splits because the appearance embedding drifts too far. The downstream mitigation is that the event structurer uses a generous `evidence_window_s` and flushes at track exit — so even a split track produces a complete event with whatever observations were accumulated before the ID change.

### Tracking multiple people simultaneously

When two people stand close together or cross paths, YOLO can temporarily merge them into a single bounding box or swap their track IDs. This creates phantom events where Person A's track suddenly receives B's observation crops, resulting in nonsense VLM output. The fix is crop padding (`crop_pad=120px`) to give the VLM enough context to identify which person is the subject, and a motion threshold filter that suppresses VLM calls when the person hasn't moved meaningfully (no point asking "what are they holding" if they're standing still at the checkout queue).

### Confidence threshold tuning

A low confidence threshold (e.g., 0.25) catches more people but fires on reflections, mannequins, and low-resolution shapes at the edge of frame. Too high (0.5+) and it misses crouching people or partially occluded figures. The current default of 0.3 was tuned against the convenience store test footage to minimize false positives while keeping real detections.

## Where it lives in the code

| File | Role |
|------|------|
| [eyas/object_detection/detector.py](../../eyas/object_detection/detector.py) | `PersonTracker` class — wraps `YOLO.track()`, filters person class, returns `Track[]` |
| [eyas/object_detection/\_\_init\_\_.py](../../eyas/object_detection/__init__.py) | Re-exports `Track`, `PersonTracker` |
