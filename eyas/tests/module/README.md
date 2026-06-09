# tests/module

Module integration tests — run real video through real components, one layer at a time.

## Tests

| Test file | What it exercises | Models needed |
|---|---|---|
| `test_module_yolo.py` | YOLO tracking on `samples/sample.mp4` | `models/yolo11n.pt` |
| `test_module_vlm.py` | YOLO + real MiniCPM-V VLM | `yolo11n.pt` + MiniCPM-V (HF) |
| `test_module_tracker_structurer.py` | YOLO + **stub** VLM + EventStructurer | `yolo11n.pt` |
| `test_reasoning_integration.py` | Reasoner against `samples/events.json` | GGUF (skipped if absent) |

## Run

```bash
pytest tests/module/ -v -s
# or run a single script directly:
python tests/module/test_module_yolo.py
```

## Environment

Set `EYAS_MODEL_PATH` to override the default GGUF path for `test_reasoning_integration.py`:

```bash
EYAS_MODEL_PATH=models/mymodel.gguf pytest tests/module/test_reasoning_integration.py -v -s
```
