# video_processing

MiniCPM-V 4.6 (1.3B) VLM wrapper — turns person crops into structured observations.

## Key exports

| Symbol | Description |
|---|---|
| `MiniCPMVLM` | Loads the model once; exposes `observe_person(frames)` and `caption_frames(frames)` |
| `PersonObservation` | Dataclass — `description`, `activity`, `held_objects`, `pickup_confirmed`, `picked_up_items` |
| `parse_person_observation(json_str)` | Parses raw LLM JSON into a `PersonObservation`, with heuristic held-object inference |
| `PERSON_STATUS_PROMPT` | System prompt sent to the VLM for every observation |
| `process_clip(path)` | Legacy helper — runs the VLM over a clip file |
| `sample_frames(frames, k)` | Uniformly sub-sample a frame list to at most `k` entries |

## Device selection

Pass `device="cuda"`, `"mps"`, or `"cpu"` to `MiniCPMVLM`.  
Use `utils.device.get_device()` to auto-detect.

## Usage

```python
from video_processing.process import MiniCPMVLM
from utils.device import get_device

vlm = MiniCPMVLM(device=get_device(), dtype="float16")
obs = vlm.observe_person(crops, track_id=1)
print(obs.activity, obs.picked_up_items)
```
