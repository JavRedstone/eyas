# MiniCPM-V 4.6 — VLM Observer

**Role in pipeline:** Stage 2 — visual observation layer  
**HF model:** [openbmb/MiniCPM-V-4.6](https://huggingface.co/openbmb/MiniCPM-V-4.6)  
**Size:** ~1.3B parameters (~2.6 GB in FP16)  
**Runtime:** Hugging Face Transformers (CPU / MPS / CUDA)  
**Sponsor:** [OpenBMB](https://www.openbmb.cn/)

---

## What it does

MiniCPM-V 4.6 is the vision-language model that watches people. After YOLO identifies a person and their bounding box, a short sequence of cropped frames from that person's observation window is handed to MiniCPM-V with a structured prompt. It returns a JSON object describing what the person is doing, what they're holding, and whether a pickup appears to have occurred.

This is the model that bridges raw pixels and structured event data. Everything downstream — event structuring, LLM reasoning, Q&A — depends on what MiniCPM-V observed.

## What the VLM is asked

The prompt asks the model to respond with structured JSON covering:

```json
{
  "description":       "Full scene description with all people visible",
  "activity":          "What the tracked person is specifically doing",
  "held_objects":      [{"name": "...", "count": 1}],
  "pickup_confirmed":  true,
  "picked_up_items":   [{"name": "...", "count": 1}]
}
```

The model receives multiple frames (evidence window, typically 2–5 crops) so it can reason about motion — a static frame might look ambiguous, but two frames showing an item moving from shelf to hand is conclusive.

## Output

```python
@dataclass
class PersonObservation:
    description:      str
    activity:         str
    held_objects:     List[Dict]   # [{"name": "...", "count": N}]
    pickup_confirmed: bool
    raw:              str          # verbatim model output, stored for auditability
    backend:          str          # "minicpmv"
```

`pickup_confirmed` is the VLM's own judgment. The event structurer may override it upward based on keyword signals in `activity` — VLMs tend to hedge, but "bends down and places item in pocket" is a pickup even if the model said `false`.

## Runtime details

```python
MODEL_ID = "openbmb/MiniCPM-V-4.6"

model = AutoModelForImageTextToText.from_pretrained(MODEL_ID, ...)
processor = AutoProcessor.from_pretrained(MODEL_ID, trust_remote_code=True)

# Inference
inputs = processor.apply_chat_template(messages, return_tensors="pt")
output = model.generate(**inputs, max_new_tokens=512)
```

Note: this uses `apply_chat_template` + `model.generate()` — the API differs from MiniCPM-o 4.5's `model.chat()`. The model is lazy-loaded on first VLM call and stays resident for the pipeline run.

## Frame sub-sampling

MiniCPM-V is too slow to run on every frame (each call is ~2–8 seconds on CPU). The event structurer maintains a sliding evidence window and sub-samples up to `evidence_frames` (default: 5) crops spaced evenly across `evidence_window_s` (default: 2 seconds). This gives the model enough temporal context to see motion without running on every frame.

## Why this model

- **Size** — 1.3B parameters is small enough to run on the CPU of a HF Spaces ZeroGPU instance without exhausting memory alongside the GGUF LLM.
- **Visual grounding** — MiniCPM-V 4.6 shows strong performance on fine-grained object recognition and spatial reasoning, which is exactly what "is that person holding a snack bar?" requires.
- **JSON output** — the model follows structured output prompts reliably enough that a simple `json.loads()` on the response works in practice, with a heuristic fallback for malformed output.
- **Sponsor** — OpenBMB is a Build Small Hackathon sponsor.

## Challenges

### VLM conservatism — the "false negative" problem

The biggest issue with MiniCPM-V for pickup detection is that the model is naturally cautious. It prefers to say "possibly picking up" or "appears to be examining" rather than committing to `pickup_confirmed: true`. This is the right epistemic instinct for a general-purpose model, but it causes consistent false negatives in a security context where under-reporting is the more serious failure mode.

The fix was a two-layer approach:
1. **Heuristic override** — the event structurer scans the `activity` text for high-confidence pickup signals ("places in pocket", "conceals", "takes from shelf", "puts in bag", etc.) and sets `pickup_confirmed=true` regardless of what the VLM's JSON field says.
2. **Pickup roster injection** — confirmed pickup events are included in a `=== CONFIRMED PICKUPS ===` block prepended to the Nemotron prompt, bypassing any re-evaluation by the LLM entirely.

### Item name bleed from scene descriptions

The VLM's `held_objects` field sometimes contained phrases like `"A blue snack bag. The person then walks toward the exit"` — the model had continued the item name into a sentence describing the next scene. This caused the LLM to see nonsense item names and fail to reason about what was taken.

The fix was `_short_item_name()`, a module-level truncation function that cuts at the first period, semicolon, or `, and` and caps at 45 characters. This strips the scene bleed without needing a second model call.

### Sensitivity tuning for pickup detection

Getting the right balance between too many false positives ("person touches shelf" → pickup) and too many false negatives ("person takes item" → not pickup) required tuning both the evidence window parameters and the keyword list used by the heuristic override. Short evidence windows (1 second) gave the model too little to reason about; long windows (4+ seconds) introduced too much noise from other activities in the same clip. The current default of 2 seconds with 5 frames was arrived at empirically against the convenience store test footage.

### API difference from MiniCPM-o

MiniCPM-V 4.6 uses `apply_chat_template` + `model.generate()` — not the `model.chat()` shorthand available in MiniCPM-o 4.5. This isn't documented prominently in the HF model card and caused integration errors early in development when code written for MiniCPM-o was reused.

## Where it lives in the code

| File | Role |
|------|------|
| [eyas/video_processing/process.py](../../eyas/video_processing/process.py) | `MiniCPMVLM` class — loads model, runs inference, parses JSON output |
| [eyas/video_processing/buffer.py](../../eyas/video_processing/buffer.py) | Evidence window and frame sub-sampling logic |
| [eyas/event_structuring/structurer.py](../../eyas/event_structuring/structurer.py) | Calls VLM per track, applies heuristic overrides to `pickup_confirmed` |
