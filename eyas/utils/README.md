# utils

Shared helpers used across the eyas package and tests.

## Modules

### `device.py`
```python
from utils.device import get_device
device = get_device()   # "cuda" | "mps" | "cpu"
```
Auto-detects the best available PyTorch backend (CUDA → MPS → CPU).

### `video.py`
```python
from utils.video import get_video_info, create_video_writer
fps, w, h = get_video_info(cap)                          # from an open VideoCapture
writer = create_video_writer("out.mp4", fps, w, h)      # mp4v VideoWriter
```

### `paths.py`
```python
from utils.paths import models_dir, fonts_dir, default_overlay_font
weights = models_dir() / "yolo11n.pt"              # absolute Path to eyas/models/
font = default_overlay_font()                       # eyas/assets/fonts/NotoSansCJKkr-Regular.otf
```

### `overlay_text.py`
Pillow-based UTF-8 labels on annotated video frames (bundled Noto Sans CJK KR font).

```python
from utils.overlay_text import OverlayLabels, FrameTextOverlay, draw_text

labels = OverlayLabels("ko")   # translates VLM text via translate_cached when locale is ko
overlay = FrameTextOverlay(frame)
overlay.draw(labels.person_label(1, "holding a bag"), (x, y), (0, 255, 0))
overlay.apply()
```

Used by `visual_pipeline.draw_tracks()` — text is drawn first, then `cv2.rectangle` boxes on top.

## Top-level re-exports

```python
from utils import get_device, get_video_info, create_video_writer, models_dir
```
