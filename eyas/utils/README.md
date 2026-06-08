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
from utils.paths import models_dir
weights = models_dir() / "yolo11n.pt"   # absolute Path to eyas/models/
```

## Top-level re-exports

```python
from utils import get_device, get_video_info, create_video_writer, models_dir
```
