# video_processing

MiniCPM-V 4.6 (1.3B) VLM wrapper — turns person crops into structured observations.

## Key exports

| Symbol | Description |
|---|---|
| `MiniCPMVLM` | Loads the model once; exposes `observe_person(frames)` and `caption_frames(frames)` |
| `LlamaCppMiniCPMVLM` | Optional MiniCPM-V 4.6 GGUF backend using `llama-cpp-python` |
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

## llama-cpp-python backend

Keep the default Transformers backend while validating the migration. The
llama.cpp backend uses the same crops, prompt, parser, and event logic.

On Apple Silicon, install a Metal-enabled build:

```bash
CMAKE_ARGS="-DGGML_METAL=on -DGGML_ACCELERATE=on" \
pip install --upgrade --force-reinstall llama-cpp-python huggingface-hub
```

The installed binding must include the modern `MTMDChatHandler`. Verify it:

```bash
python -c "from llama_cpp.llama_chat_format import MTMDChatHandler; print('mtmd ready')"
```

If that import fails, build the Python binding from source instead of using a
cached wheel:

```bash
CMAKE_ARGS="-DGGML_METAL=on -DGGML_ACCELERATE=on" \
pip install --upgrade --force-reinstall --no-binary llama-cpp-python \
  llama-cpp-python
```

Download both F16 GGUF files locally:

```bash
hf download openbmb/MiniCPM-V-4.6-gguf \
  --include "*F16.gguf" \
  --include "*mmproj*" \
  --local-dir models/minicpmv
```

Run the official F16 GGUF directly from the Hugging Face cache:

```bash
python scripts/run_visual_pipeline.py input/test2.mp4 \
  --device mps \
  --vlm-backend llama-cpp-python \
  --llama-filename MiniCPM-V-4_6-F16.gguf \
  --output-dir output/llama-f16
```

To use a previously downloaded model file, add:

```bash
--llama-model-path models/minicpmv/MiniCPM-V-4_6-F16.gguf \
--llama-mmproj-path models/minicpmv/mmproj-model-f16.gguf
```

Start with F16 to preserve accuracy. Benchmark Q8 or Q4 only after comparing
their `events.json` output against F16. MiniCPM-V 4.6 multimodal support
requires a recent llama-cpp-python/libmtmd build; older releases fail with a
clear upgrade message.

MiniCPM-V 4.6 requires llama.cpp release `b9049` or newer. When validating the
files with native llama.cpp, use `llama-mtmd-cli` and pass `--reasoning off`
for the Instruct checkpoint:

```bash
llama-mtmd-cli \
  -m models/minicpmv/MiniCPM-V-4_6-F16.gguf \
  --mmproj models/minicpmv/mmproj-model-f16.gguf \
  -c 8192 --reasoning off --image test.jpg \
  -p "Describe only what is visible."
```
