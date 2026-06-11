# models

Local model weight files — not tracked in git.

## Expected files

| File | Used by | Notes |
|---|---|---|
| `yolo11n.pt` | `object_detection/` | YOLO11-nano; download from Ultralytics or train locally |
| `nemotron-nano-4b.gguf` | `llm/` | Default GGUF LLM; override with `EYAS_MODEL_PATH` env var |
| `minicpmv/MiniCPM-V-4_6-F16.gguf` | `video_processing/` | Optional F16 llama-cpp-python VLM backend |
| `minicpmv/mmproj-model-f16.gguf` | `video_processing/` | MiniCPM-V 4.6 vision projector |

## Downloading

```bash
# YOLO weights (auto-downloaded by Ultralytics on first run)
python -c "from ultralytics import YOLO; YOLO('yolo11n.pt')"

# GGUF model — example using huggingface-cli
huggingface-cli download <repo> nemotron-nano-4b.gguf --local-dir models/
```

MiniCPM-V 4.6 weights are fetched automatically by `transformers` on first use and cached in the HuggingFace hub cache (`~/.cache/huggingface/`).

The llama-cpp-python backend also defaults to the Hugging Face cache. Pass
`--llama-model-path models/minicpmv/MiniCPM-V-4_6-F16.gguf` to use a model
stored under this directory instead. Also pass the matching projector with
`--llama-mmproj-path`.

Download both files with separate include flags:

```bash
hf download openbmb/MiniCPM-V-4.6-gguf \
  --include "*F16.gguf" \
  --include "*mmproj*" \
  --local-dir models/minicpmv
```
