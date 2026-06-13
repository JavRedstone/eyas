# Field Notes — Building Eyas

*A build log from the Build Small Hackathon. Eyas is an offline CCTV intelligence agent that turns raw footage into a structured security event log using a chain of small models — YOLO11n → MiniCPM-V 4.6 → Nemotron 3 Nano 4B — all running locally with no cloud APIs.*

---

## Why this project

The problem is embarrassingly concrete. A convenience store owner we know has CCTV cameras covering the entrance, counter, and back door. When something goes missing or a dispute arises, reviewing footage means sitting with a laptop and scrubbing through four to eight hours of video. It takes 30–60 minutes of tedious skimming to find a two-minute window.

The usual pitch for "AI security cameras" is a cloud subscription that ships footage off-site, stores it indefinitely, and charges per camera per month. That is not what a small shop owner wants to sign up for.

The question we started with: can a chain of genuinely small models — the kind that fit on a laptop — do something useful with CCTV footage, entirely locally?

---

## The pipeline design

We went through several designs before landing on the one we shipped.

**First instinct: VLM end-to-end.** Run the vision-language model directly on video. Every N frames, ask the VLM "is anything suspicious happening?" This worked in the notebook but was painfully slow (MiniCPM-V 4.6 on CPU takes 3–8 seconds per image, not per second of video) and produced a wall of narrative text with no structure. We could not reliably extract *when* or *where* from the output.

**What we actually shipped:** a three-stage chain where each model does only what it is good at.

```
YOLO11n (6 MB)          — detect and track people frame by frame
     ↓  track crops
MiniCPM-V 4.6 (1.3B)   — observe each tracked person, produce structured JSON
     ↓  PersonObservation[]
heuristic structurer    — convert observations into typed events with timestamps
     ↓  Event[]
Nemotron 3 Nano 4B      — reason over the event log, answer questions, write the report
```

The heuristic structurer in the middle turned out to be the most important piece. It converts the VLM's free-form observations into a crisp event log before the LLM ever sees them. The LLM never has to look at pixels; it reasons over structured JSON. This made the LLM's job much easier and its outputs far more consistent.

---

## Lessons from each stage

### YOLO + BotSORT: fast and reliable, but crops are everything

YOLO11n is impressively fast even on CPU — about 30–80 ms per frame depending on scene complexity. BotSORT tracking is solid across most camera angles.

The tricky part was deciding which frames to send to the VLM. Sending every frame per track would take hours. We settled on sub-sampling to at most `k` frames per track (currently k=4), selecting frames spread across the track's lifetime to capture entry, mid-dwell, and exit states.

The crop size matters more than we expected. If a person is partially visible or in poor lighting, the VLM produces vague or hedged descriptions. We added padding to bounding boxes (15% on each side) which improved VLM confidence noticeably.

### MiniCPM-V 4.6: surprisingly good at CCTV, with one major catch

MiniCPM-V 4.6 was not trained on security footage, but it turned out to be a reasonable observer. Give it a crop of someone reaching toward a shelf and it will often correctly note "person appearing to pick up or handle item." Give it someone lingering near an exit and it notes the positioning. It does not pretend to see things it cannot.

The major catch: **it will not confirm a pickup unless it is confident.** The model is well-calibrated about uncertainty, which means `pickup_confirmed: false` is the common case even for genuine pickups captured at low resolution or from an oblique angle. We ended up leaning on the heuristics more than the VLM's explicit judgment — the VLM's description text was more useful than its boolean output.

We prompt the VLM to return structured JSON (`description`, `activity`, `held_objects`, `pickup_confirmed`). In practice the JSON is parseable about 85% of the time; the rest requires a fallback extraction pass. We have a `_try_parse_vlm_json` helper that strips markdown fences, handles trailing commas, and falls back to regex extraction for the fields we need. Not elegant, but robust.

### Event structuring: the glue nobody talks about

This layer has no model. It is a set of heuristics over the observation stream: dwell time per zone, pickup confirmation threshold, track-exit events, loitering detection.

Getting this right took longer than any of the model integrations. The hardest part: when to emit an event. If you emit too eagerly (after a single frame's observation) you get noise. If you wait too long (flush only when a track ends) you miss events for long-duration loiterers. We ended up with a sliding evidence buffer — emit an event when either (a) the track ends or (b) the buffer exceeds a frame threshold with consistent evidence for a given event type.

Zone assignment uses configurable polygons from the filename convention (`20240608_120000_entrance.mp4` → zone `entrance`). A fallback zone covers the full frame when the filename does not match the pattern. This was the right call for the demo — it means the system works on arbitrary uploaded footage without any configuration.

### Nemotron 3 Nano 4B: fast enough, but prompting is everything

Nemotron 3 Nano 4B via llama-cpp-python is the reasoning layer. It handles summarization, risk assessment, natural-language Q&A, and the TTS script.

On CPU (M-series Mac), the Q4_K_M GGUF runs at roughly 12–18 tokens/second. For a summary of 15–20 events, this is 15–25 seconds of wait time — acceptable for a security review tool that is not real-time. On HF Spaces CPU (shared x86), it is closer to 4–7 tokens/second, which is slow but usable.

The prompt structure matters enormously. Asking the LLM to reason over a raw JSON dump of events and return a free-form summary produces acceptable results. Asking it to return structured JSON (`risk_level`, `flags[]`, `suspicious_clips[]`, `summary`) produces inconsistent output without constrained decoding. We use llama.cpp's grammar-constrained generation for the structured endpoints and free-form generation for Q&A and the audio script. The quality gap is significant — structured outputs with grammar constraints are reliable; without them, field extraction requires post-processing.

One thing we did not fully solve: the LLM's context window is 4,096 tokens, and a busy night's event log (50+ events with VLM descriptions) can exceed that. We truncate by recency and priority (pickups and high-confidence events first), but the right answer is a retrieval step that we did not have time to implement.

### Translation (TinyAya): cheaper than you'd think

TinyAya handles Korean translation of LLM outputs. It runs via llama-cpp-python and caches outputs per source string. In practice, translation is fast (~2–4 seconds per short paragraph) and the quality is good enough for a security summary context.

We only translate LLM-generated text (summary, alert narrative). UI strings are a static i18n table. This distinction matters for performance — you do not want to round-trip every UI label through a GGUF model.

### VoxCPM2 TTS: the fun feature that does not run on CPU

VoxCPM2 (MiniCPM-o-2_6) produces natural-sounding speech from the event summary. On a machine with CUDA it is genuinely impressive — the audio brief sounds like a calm security system readout.

The problem: it requires CUDA. On HF Spaces CPU tier and on machines without a GPU, we skip TTS gracefully (the Audio Report tab shows an explanatory message). This is the one part of the pipeline that is not truly CPU-friendly, and we knew it going in. The architecture marks TTS as optional throughout; if `torch.cuda.is_available()` is false, the endpoint returns an empty audio object and the UI adapts.

---

## The frontend decision

The hackathon requires a Gradio app. It does not require a Gradio *UI*.

Gradio's `gr.Server` lets you serve static files from a path while still exposing all the pipeline logic as Gradio API endpoints. The React frontend communicates with Gradio via `@gradio/client` exactly as the default UI would; from Gradio's perspective nothing is different.

This was worth doing. The default Gradio UI makes tabbed analysis tools look like form submissions. A proper SPA with resizable split panels, a scatter-chart event timeline, and a live-updating pipeline progress view changes how the tool *feels* to use. The shop owner we built this for understood what the annotated video and event table were within 30 seconds. That would not have happened with a Gradio Dataframe and a Gradio Video component on the same page.

The cost: the custom UI takes real time to build and debug. We spent roughly a third of the build time on the frontend. For a hackathon that comes at the expense of more model experimentation, but we think it was right for the Backyard AI track, where "polished Gradio app" is an explicit judging criterion.

---

## What surprised us

**The small models are honest.** MiniCPM-V and Nemotron consistently hedge when they are uncertain rather than hallucinating confident answers. For a security tool this is exactly what you want — a false alarm is less damaging than a false confidence.

**The heuristic layer is where the product lives.** The models handle perception and reasoning. The heuristic structurer in the middle handles the domain: what counts as an event, what makes it significant, which zone it belongs to. Improving the heuristics had a larger impact on output quality than upgrading model parameters.

**CPU inference is viable for this use case.** A shop owner does not need real-time analysis — they upload last night's footage in the morning. Processing a 30-minute clip takes 8–12 minutes on CPU (most of that is VLM inference). For the actual use case — morning review of overnight footage — this is fine.

**The llama.cpp GGUF ecosystem is in good shape.** Two years ago running a 4B LLM via llama-cpp-python with grammar-constrained JSON output would have required significant effort. Today it is a pip install and a context manager.

---

## What we would do differently

- **Retrieval over the event log.** A 4k token context window hits its limit quickly. A small embedding model indexing events, with retrieval before the LLM call, would make Q&A much more reliable across long recordings.

- **Better frame selection for VLM.** Sub-sampling k=4 frames per track is simple but misses important moments. Motion-based keyframe selection — frames with the highest optical flow magnitude — would capture the most information-dense moments per track.

- **Fine-tune YOLO on retail footage.** YOLO11n is not trained on CCTV footage specifically. A fine-tuned checkpoint on retail surveillance datasets would improve tracking at the camera angles and resolutions common in small stores (high-angle, wide-FOV, lower resolution).

- **Make TTS CPU-viable.** VoxCPM2 requiring CUDA makes the audio brief feel like a premium feature unavailable on the cheapest hardware. A smaller TTS model (Kokoro, Piper) running on CPU would make the feature universally available.

---

## Model and tool credits

- [YOLO11n](https://github.com/ultralytics/ultralytics) — Ultralytics
- [MiniCPM-V 4.6](https://huggingface.co/openbmb/MiniCPM-V-4.6) — OpenBMB
- [Nemotron 3 Nano 4B GGUF](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF) — NVIDIA
- [TinyAya](https://huggingface.co/CohereLabs/tiny-aya-global-GGUF) — Cohere Labs
- [VoxCPM2 / MiniCPM-o-2_6](https://huggingface.co/openbmb/MiniCPM-o-2_6) — OpenBMB
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) — Andrei Betlen et al.
- [React](https://react.dev/), [Vite](https://vitejs.dev/), [MUI](https://mui.com/), [Recharts](https://recharts.org/), [Framer Motion](https://www.framer.com/motion/)

---

*Eyas is open source. Space: [build-small-hackathon/eyas](https://huggingface.co/spaces/build-small-hackathon/eyas)*
