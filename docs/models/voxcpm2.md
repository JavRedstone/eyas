# VoxCPM2 — Text-to-Speech

**Role in pipeline:** Postprocessing — audio report  
**HF model:** [openbmb/VoxCPM2](https://huggingface.co/openbmb/VoxCPM2)  
**Size:** ~2.4B parameters  
**Runtime:** `voxcpm` Python package (MPS / CPU / ZeroGPU) or `nanovllm_voxcpm` (dedicated CUDA only)  
**Sponsor:** [OpenBMB](https://www.openbmb.cn/)

---

## What it does

VoxCPM2 converts the LLM's written security brief into a spoken audio report. After the operator clicks "Generate Audio Report", the pipeline:

1. Calls `generate_alert()` on the Nemotron reasoner to produce a concise spoken-style script
2. Passes the text to VoxCPM2
3. Streams `(sample_rate, audio_chunk)` pairs back to the frontend as the model synthesizes
4. The browser plays the audio directly in the Audio Report tab

The result is a hands-free spoken summary an operator can listen to without looking at the screen.

## Backends

VoxCPM2 has two runtime paths in Eyas depending on the hardware:

### Standard (`voxcpm`)

```python
from voxcpm import VoxCPM
model = VoxCPM.from_pretrained("openbmb/VoxCPM2", device="auto", load_denoiser=False)
```

Used on ZeroGPU (HF Spaces burst GPU), MPS (Apple Silicon), and CPU. `device="auto"` selects the best available device. `load_denoiser=False` skips the optional audio enhancement stage to reduce memory usage and latency.

### High-throughput (`nanovllm_voxcpm`)

```python
_voxcpm2_nano_server = SyncVoxCPMServerPool(...)
```

Used on dedicated CUDA machines (not ZeroGPU). This backend is a persistent server pool for lower per-request latency. Do not use on ZeroGPU — the persistent process conflicts with ZeroGPU's ephemeral GPU allocation model.

## Graceful degradation

VoxCPM2 requires a GPU or MPS device for reasonable performance. If neither is available and generation would be too slow, Eyas skips TTS silently and the Audio Report tab shows an error message rather than hanging. The rest of the pipeline (events, summary, Q&A) is unaffected.

## Output

```python
# sample_rate: int (from model config)
# audio: np.ndarray of float32 samples
(sample_rate, audio) = model.tts(text)
```

The frontend receives this as a base64-encoded WAV and plays it in a standard `<audio>` element.

## Challenges

### ZeroGPU memory conflicts

VoxCPM2 at ~2.4B parameters is the second-largest model in the stack. On HF Spaces ZeroGPU, it competes with MiniCPM-V for the burst GPU allocation. The initial implementation loaded both models simultaneously, which caused OOM errors on the ZeroGPU instance.

The solution was strict sequential model ownership: MiniCPM-V is unloaded (model set to `None`, CUDA cache cleared) before VoxCPM2 loads, and VoxCPM2 is unloaded before the next pipeline run. This means audio generation can't happen in parallel with video analysis, but on a single GPU that's unavoidable.

### Two incompatible backends

VoxCPM2 has two Python packages: `voxcpm` (the official package, supports MPS/CPU/ZeroGPU) and `nanovllm_voxcpm` (a high-throughput server pool, CUDA-only, persistent process). These can't both be installed on the same machine because they conflict on shared CUDA state. Eyas handles this by detecting which package is available at startup and routing to the appropriate `get_voxcpm2_model()` variant.

The `nanovllm_voxcpm` backend was initially added for dedicated GPU machines but had to be removed from `requirements.txt` before HF deployment because it caused the HF Spaces build to fail — the CUDA wheel it required wasn't available in the HF build environment.

### Compute time on CPU

VoxCPM2 TTS on CPU for a 30-second audio report takes several minutes — longer than the analysis that produced it. The fix was `load_denoiser=False` (skips the optional audio enhancement step, halves processing time) and constraining the input script length. The Nemotron `generate_alert()` prompt is written to produce concise, spoken-style output rather than the full verbose summary, keeping audio generation under 60 seconds on CPU.

### Model loading time on cold start

HF Spaces ZeroGPU instances cold-start with no model loaded. VoxCPM2's first load (downloading weights + initialization) takes 30–120 seconds depending on network and instance warmth. Eyas shows a loading splash with per-model progress indicators so the operator knows what's happening, and VoxCPM2 is listed last since it's the least critical path (audio is optional; events and summary are not).

## Why this model

- **Same model family** — VoxCPM2 is from the same OpenBMB ecosystem as MiniCPM-V 4.6. Using both keeps the dependency footprint tight and consistent.
- **Integrated TTS** — no separate TTS model (like Coqui or Bark) needed; VoxCPM2 handles speech synthesis in one package.
- **Streaming** — VoxCPM2 can stream chunks as they're synthesized rather than waiting for the full audio to complete, which improves perceived latency for longer reports.
- **Sponsor** — OpenBMB is a Build Small Hackathon sponsor.

## Where it lives in the code

| File | Role |
|------|------|
| [eyas/postprocessing/\_\_init\_\_.py](../../eyas/postprocessing/__init__.py) | `get_voxcpm2_model()` and `get_voxcpm2_model_nano()` — lazy-load both backends |
| [eyas/ui/gradio_app.py](../../eyas/ui/gradio_app.py) | `/generate_audio` endpoint — calls the appropriate backend, streams audio chunks |
| [eyas/ui/frontend/src/components/tabs/AudioReport.jsx](../../eyas/ui/frontend/src/components/tabs/AudioReport.jsx) | Frontend tab — triggers generation, shows progress phases, plays audio |
