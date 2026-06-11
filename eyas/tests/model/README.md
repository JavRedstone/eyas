# tests/model

Model integration tests — run real video or real text through real components, one model at a time.

## Tests

| Test file | What it exercises | Models needed |
|---|---|---|
| `test_module_yolo.py` | YOLO tracking on `samples/sample.mp4` | `models/yolo11n.pt` |
| `test_module_vlm.py` | YOLO + real MiniCPM-V VLM | `yolo11n.pt` + MiniCPM-V (HF) |
| `test_module_tracker_structurer.py` | YOLO + **stub** VLM + EventStructurer | `yolo11n.pt` |
| `test_reasoning_integration.py` | Reasoner against `samples/events.json` | GGUF (skipped if absent) |
| `test_translation.py` | `translate()` with real TinyAya GGUF | `llama-cpp-python` |
| `test_tts.py` | `tts()` with real VoxCPM2; CUDA for streaming | `voxcpm`; CUDA for streaming |

## Run

```bash
pytest tests/model/ -v -s
# or run a single file directly:
python tests/model/test_module_yolo.py
```

## Environment

Set `EYAS_MODEL_PATH` to override the default GGUF path for `test_reasoning_integration.py`:

```bash
EYAS_MODEL_PATH=models/mymodel.gguf pytest tests/model/test_reasoning_integration.py -v -s
```
