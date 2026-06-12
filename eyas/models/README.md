# models

Local model weight files — **not tracked in git** (gitignored). All models download automatically on first run.

## Expected files

| File | Used by | How it's obtained |
|---|---|---|
| `yolo11n.pt` | `object_detection/` | Downloaded by Ultralytics on first use, or by `eyas/scripts/download_models.py` |
| `nemotron-nano-4b.gguf` | `llm/` | Override path; default is the HF cache (`Llama.from_pretrained`) |
| `minicpmv/MiniCPM-V-4_6-F16.gguf` | `video_processing/` | Optional — for the llama-cpp-python VLM backend |
| `minicpmv/mmproj-model-f16.gguf` | `video_processing/` | Matching vision projector for the GGUF backend |

## Auto-download (default)

- **YOLO**: `ultralytics` fetches `yolo11n.pt` automatically on first call to `PersonTracker`
- **Nemotron**: `llama_cpp.Llama.from_pretrained("nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF")` downloads `NVIDIA-Nemotron3-Nano-4B-Q4_K_M.gguf` to the HF hub cache
- **TinyAya**: `huggingface_hub.hf_hub_download("CohereLabs/tiny-aya-global-GGUF")` downloads to the HF cache
- **MiniCPM-V**: `transformers` fetches weights on first `MiniCPMVLM` instantiation
- **VoxCPM2**: downloads on first TTS call

## Docker build pre-download

`eyas/scripts/download_models.py` runs during `docker build` to bake YOLO and the two GGUF models into the image layer, avoiding cold-start delays.

## llama-cpp-python VLM backend (optional)

To use MiniCPM-V via llama.cpp instead of Transformers, download both GGUF files:

```bash
hf download openbmb/MiniCPM-V-4.6-gguf \
  --include "*F16.gguf" \
  --include "*mmproj*" \
  --local-dir eyas/models/minicpmv
```

Then pass `--vlm-backend llama-cpp-python` to `eyas/scripts/run_visual_pipeline.py`. See [`docs/LLAMA_CPP.md`](../../docs/LLAMA_CPP.md) for full instructions.
