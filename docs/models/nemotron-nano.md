# Nemotron 3 Nano 4B — LLM Reasoner

**Role in pipeline:** Stage 4 — reasoning and summarization  
**HF model:** [nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF)  
**File:** `NVIDIA-Nemotron3-Nano-4B-Q4_K_M.gguf`  
**Size:** ~2.5 GB (Q4_K_M quantized)  
**Runtime:** [llama-cpp-python](../architecture/LLAMA_CPP.md) (CPU / Metal / CUDA)  
**Context window:** 4096 tokens  
**Sponsor:** [NVIDIA](https://www.nvidia.com/)

---

## What it does

After the visual pipeline finishes and the event list is assembled, Nemotron 3 Nano reads the full event log and reasons over it. It produces structured JSON with a plain-language summary, a list of security flags, a risk level, and a list of suspicious clips to review. It also powers the "Ask Footage" Q&A tab — the operator can type a question and Nemotron answers it using the event log as context.

Nemotron is the model that turns a raw log of timestamped observations into actionable security intelligence.

## Functions

### `summarize_events(events)`

Reads the trimmed event log and returns:

```json
{
  "summary":          "Narrative description of the session",
  "flags":            ["theft", "loitering"],
  "risk_level":       "high",
  "suspicious_clips": ["t=5.84s (counter)", "t=14.2s (entrance)"]
}
```

The prompt injects a `=== CONFIRMED PICKUPS ===` roster of any events where `pickup_confirmed=true` before the event log, so the model cannot overlook confirmed pickups even under context pressure.

### `answer_query(events, query, summary)`

Answers a natural-language question about the footage. The session summary is injected as authoritative ground truth before the event log — the model is instructed not to contradict the summary and to use the event log only for specific timestamps and indices.

### `generate_alert(event)`

Produces a one-sentence alert for a single high-priority event (used by the TTS audio report path).

## Runtime

Nemotron is loaded via `llama-cpp-python`:

```python
Llama.from_pretrained(
    repo_id="nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF",
    filename="NVIDIA-Nemotron3-Nano-4B-Q4_K_M.gguf",
    n_ctx=4096,
    n_gpu_layers=-1,   # -1 = all layers on GPU if available
)
```

On HF Spaces ZeroGPU, `n_gpu_layers=-1` offloads all layers to the burst GPU. On CPU-only environments (including HF free tier), it runs in pure CPU mode at ~1–3 tokens/second. On Apple Silicon, Metal acceleration is used automatically.

The model is **lazy-loaded** on the first reasoning call and released after use to free Metal/GPU memory for the next pipeline run.

## Event trimming

The event log is trimmed to fit the 4096-token context. Trimming strategy:
- Multi-camera sessions: distribute the budget proportionally across cameras so each camera gets representation
- Single camera: most recent events are kept; early boilerplate observations are dropped first
- Confirmed pickup events are never trimmed — they're included in the guaranteed pickup roster instead

## Why this model

- **Size** — 4B Q4_K_M fits comfortably in ~2.5 GB RAM, leaving headroom for MiniCPM-V's activations and the rest of the pipeline.
- **Instruction following** — Nemotron 3 Nano follows structured JSON output prompts reliably for its size class, reducing the need for grammar-constrained decoding.
- **No API** — GGUF via llama.cpp means zero latency, zero cost, zero data leaving the device.
- **Sponsor** — NVIDIA is a Build Small Hackathon sponsor.

## Challenges

### Context window pressure

At 4096 tokens, Nemotron's context fills fast. A multi-camera session with 4 cameras and 10+ events per camera can easily produce an event log that doesn't fit. The naive approach — just pass all events and let the model truncate — caused the worst events to be cut and the model to conclude "no suspicious activity detected" for a session that had a confirmed pickup at t=5s.

The trimming strategy went through several iterations:
- **Naive tail-trim** (first attempt): keep the most recent N events. This dropped early pickups.
- **Pickup-safe trim** (second attempt): never trim events where `pickup_confirmed=true`. This fixed the core false-negative case but didn't help multi-camera balance.
- **Budget-per-camera trim** (final): in multi-camera sessions, divide the 2400-character event budget proportionally across cameras. Each camera gets at least a floor budget regardless of event count, so a camera with one pickup event isn't crowded out by a camera with 15 mundane observations.

### LLM contradicting its own earlier analysis

In multi-camera sessions, Nemotron was asked to produce a total summary that incorporated per-camera summaries already generated. It would sometimes issue a total summary saying "no suspicious activity" despite the per-camera summaries containing a confirmed pickup — because the total summary call saw only the raw event log, not the per-camera conclusions.

The fix was two-pronged:
1. Inject the `=== CONFIRMED PICKUPS ===` roster at the top of every prompt, making confirmed pickups impossible to overlook.
2. Wire the session summary into the Q&A prompt as authoritative context — Q&A answers are now explicitly instructed to treat the summary as ground truth and only use the event log for specific timestamps.

### Risk level comparison bug

The `combinedSummary` aggregation in the frontend computed `maxRisk` by comparing risk level strings directly (`"high" > "medium"` is alphabetically false in JS). This caused "medium" sessions to be reported as "high" and vice versa when aggregating multiple clips. Fixed by mapping risk levels to an integer `riskOrder` and comparing numerically.

### Slow inference on CPU

At ~1–3 tokens/second on CPU, generating a full security summary takes 30–90 seconds. This is acceptable for a batch analysis workflow but felt slow in Q&A. The mitigation was keeping the LLM context short (2400 chars of event text max), trimming aggressively, and lazy-unloading the model after each call to return GPU/Metal memory to MiniCPM-V for the next pipeline run.

## Where it lives in the code

| File | Role |
|------|------|
| [eyas/llm/reasoner.py](../../eyas/llm/reasoner.py) | `LlamaBackend` + `Reasoner` — loads model, trims events, runs summarize/QA/alert |
| [eyas/llm/prompts.py](../../eyas/llm/prompts.py) | All prompt templates: `SUMMARY_PROMPT`, `QA_PROMPT`, `ALERT_PROMPT` |
