# streaming

Live camera capture with on-demand clip recording.

## Key exports

| Symbol | Description |
|---|---|
| `StreamCapture` | Manages a background capture thread; exposes `get_rgb()`, `start_recording()`, `stop_recording()` |

## Usage

```python
from streaming.capture import StreamCapture

cap = StreamCapture()
cap.start(0)               # device index or RTSP URL

frame = cap.get_rgb()      # latest frame as RGB ndarray, or None

cap.start_recording()
# ... some time passes ...
clip_path = cap.stop_recording()   # returns path to saved .mp4

cap.stop()
```

## Notes

- Requires `opencv-python`.
- Recorded clips are written to the `clips/` directory alongside the package.
- `frame_size()` and `capture_fps()` return the actual values from the hardware, or sensible defaults before `start()` is called.
