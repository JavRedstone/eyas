# Eyas — AI Security Camera Agent

*Field Notes from the Build Small Hackathon. Eyas, which stands for a* small *hawk, is an offline CCTV intelligence agent that turns raw footage into a structured security event log using a chain of* small *models: YOLO11n → MiniCPM-V 4.6 → Nemotron 3 Nano 4B → TinyAya → VoxCPM2 — all running locally with no cloud APIs.*

#### Project Links

- [Live Demo](https://huggingface.co/spaces/build-small-hackathon/eyas)
- [Source Code](https://huggingface.co/spaces/build-small-hackathon/eyas/tree/main)
- [Social Media Post](https://www.linkedin.com/feed/update/urn:li:activity:7472122729828364288/)
- [Demo Video](https://www.youtube.com/watch?v=x9h7nMv_KeQ)

---

## Why we built this

<figure>
  <audio controls src="https://cdn-uploads.huggingface.co/production/uploads/667db115d29e971c591a8031/Q3pRX9Gr0n6CcKeq6973O.mpga"></audio>
  <figcaption>
    <strong>Audio 1.</strong> Interview with one of our teammate's family who runs a retail shop (Korean)
  </figcaption>
</figure>

Our motivation for building this is quite straightforward.

One of our teammates has family who runs a small retail shop, and shoplifting is a problem they experience firsthand. 

Like many small businesses, they already have CCTV cameras covering the aisles, entrance, and counter. But in reality, it is impossible to constantly watch every camera, especially when there are multiple groups of customers in the store at the same time. Shoplifters often take advantage of those busy moments.

Even when the owner is almost certain that something has been stolen, they cannot immediately accuse someone without first reviewing the footage and confirming what happened. By the time they check the video, verify the incident, and understand what was taken, the person has usually already left the store.

The financial loss is only one part of the problem. The emotional toll can be even greater.

That is why this problem felt worth solving to us.

Repeated theft makes owners more suspicious of customers, creates constant stress, and can ruin their entire day. Because each incident may seem small on its own, shoplifting is often not treated as a high priority. Over time, many small business owners simply stop reporting it.

But ignoring the problem does not make it disappear. In many cases, the same people continue stealing, not only from one store, but from many others.

We believe the key may not be harsher punishment, but immediate deterrence.

If a theft attempt can be detected the moment it happens and staff can be alerted right away, the shoplifter realizes that stealing from this store is not easy. More importantly, the owner gets a chance to respond before the person leaves.

> **"Security cameras are usually used to identify a shoplifter after an incident has already happened."**  
> <small>보안카메라는 보통 일이 다 끝난 다음에 절도자를 확인하는 용도로 쓰이잖아요.</small>

That is the gap we want to address. Instead of using CCTV only after the fact, we want to help store owners use it in the moment.

> **"A simple alert like 'you might want to check this' would allow us to act right away and potentially prevent shoplifting."**  
> <small>지금처럼 "이건 확인이 한 번 필요하다"는 식으로 알려주기만 해도, 바로 움직여서 상황을 막을 수 있거든요.</small>

An AI-powered detection system could identify suspicious behavior, notify employees immediately, and give them the opportunity to respond before a theft is completed.

The goal is not to accuse people automatically or replace human judgment. The goal is to give small business owners an extra set of eyes when they cannot watch everything themselves.

For stores with limited staff, this kind of system could help protect not only their inventory, but also their peace of mind.

---

## The pipeline design

<figure>
  <img src="https://media.githubusercontent.com/media/JavRedstone/eyas/refs/heads/main/docs/assets/eyas-architecture-diagram.png" alt="Eyas architecture diagram">
  <figcaption><strong>Figure 1.</strong> Eyas architecture diagram. Raw CCTV footage is processed locally through YOLO11n for detection, MiniCPM-V 4.6 for visual analysis, and Nemotron 3 Nano 4B for structured event-log reasoning.</figcaption>
</figure>

We went through several designs before landing on the one we shipped.

### Our first instinct: VLM end-to-end

Run the vision-language model directly on video. Every `N` frames, ask the VLM "is anything suspicious happening?" This worked in the notebook but was painfully slow (MiniCPM-V 4.6 on CPU takes 3–8 seconds per image, not per second of video) and produced a wall of narrative text with no structure. We could not reliably extract *when* or *where* from the output.

### What we actually shipped: a three-stage chain where each model does only what it is good at

```
YOLO11n (6 MB)          — detect and track people frame by frame
     ↓  track crops
MiniCPM-V 4.6 (1.3B)   — observe each tracked person, produce structured JSON
     ↓  PersonObservation[]
heuristic structurer    — convert observations into typed events with timestamps
     ↓  Event[]
Nemotron 3 Nano 4B      — reason over the event log, answer questions, write the report
```

The heuristic structurer in the middle turned out to be the most important piece. It converts the VLM's free-form observations into event logs before the LLM ever sees them. The LLM never has to look at the raw pixels. Instead it reasons over structured JSON of the actual events. This made the LLM's job much easier and its outputs far more consistent.

---

## Lessons from each stage

### YOLO + BotSORT: fast and reliable, but crops are everything

YOLO11n is impressively fast even on CPU — about 30–80 ms per frame depending on scene complexity. BotSORT tracking is solid across most camera angles.

The tricky part was deciding which frames to send to the VLM. Sending every frame per track would take hours. We settled on sub-sampling to at most `k` frames per track (currently k=4), selecting frames spread across the track's lifetime to capture entry, mid-dwell, and exit states.

The crop size mattered more than we expected. If a person is partially visible or in poor lighting, the VLM produces vague or incorrect descriptions. We added padding to bounding boxes (15% on each side) which improved VLM confidence and gave the model enough context to identify interactions between the person and nearby objects.

### MiniCPM-V 4.6: surprisingly good at CCTV, with one major catch

https://cdn-uploads.huggingface.co/production/uploads/667db115d29e971c591a8031/UKcQLiZujktPQ2RD8_wF7.qt
<figcaption><strong>Video 1.</strong> Example VLM observation from a CCTV crop. MiniCPM-V 4.6 does not directly confirm theft, but describes visible actions such as a person reaching toward, picking up, or handling an item.</figcaption>

MiniCPM-V 4.6 was not trained on security footage, but it turned out to be a reasonable observer. Give it a crop of someone reaching toward a shelf and it will often correctly note "person appearing to pick up or handle item." Give it someone lingering near an exit and it notes the positioning. It does not pretend to see things it cannot.

The major catch: **it will not confirm a pickup unless it is confident.** The model is well-calibrated about uncertainty, which means `pickup_confirmed: false` is the common case even for genuine pickups captured at low resolution or from an oblique angle. We ended up leaning on the heuristics more than the VLM's explicit judgment — the VLM's description text was more useful than its boolean output.

We prompt the VLM to return structured JSON (`description`, `activity`, `held_objects`, `pickup_confirmed`). In practice the JSON is parseable about 85% of the time; the rest requires a fallback extraction pass. We have a `_try_parse_vlm_json` helper that strips markdown fences, handles trailing commas, and falls back to regex extraction for the fields we need.

### Event structuring: the glue nobody talks about

This layer has no model. It is a set of heuristics over the observation stream: dwell time per zone, pickup confirmation threshold, track-exit events, loitering detection.

Getting this right took longer than any of the model integrations. The hardest part: when to emit an event. If you emit too eagerly (after a single frame's observation) you get noise. If you wait too long (flush only when a track ends) you miss events for long-duration loiterers. We ended up with a sliding evidence buffer — emit an event when either (a) the track ends or (b) the buffer exceeds a frame threshold with consistent evidence for a given event type.

Zone assignment uses configurable polygons from the filename convention (`20240608_120000_entrance.mp4` → zone `entrance`). A fallback zone covers the full frame when the filename does not match the pattern. This was the right call for the demo — it means the system works on arbitrary uploaded footage without any configuration.

### Nemotron 3 Nano 4B: fast enough, but prompting is everything

https://cdn-uploads.huggingface.co/production/uploads/667db115d29e971c591a8031/jhM_YmkKLJnIC1GpsKg35.qt
<figcaption><strong>Video 2.</strong> Example footage of Nemotron 3 Nano 4B handling natural-language Q&A tasks.</figcaption>

Nemotron 3 Nano 4B via llama-cpp-python is the reasoning layer. It handles summarization, risk assessment, natural-language Q&A, and the TTS script.

On CPU (M-series Mac), the Q4_K_M GGUF runs at roughly 12–18 tokens/second. For a summary of 15–20 events, this is 15–25 seconds of wait time — acceptable for a security review tool that is not real-time. On HF Spaces CPU (shared x86), it is closer to 4–7 tokens/second, which is slow but usable.

The prompt structure matters enormously. Asking the LLM to reason over a raw JSON dump of events and return a free-form summary produces acceptable results. Asking it to return structured JSON (`risk_level`, `flags[]`, `suspicious_clips[]`, `summary`) produces inconsistent output without constrained decoding. We use llama.cpp's grammar-constrained generation for the structured endpoints and free-form generation for Q&A and the audio script. The quality gap is significant — structured outputs with grammar constraints are reliable; without them, field extraction requires post-processing.

One thing we did not fully solve: the LLM's context window is 4,096 tokens, and a busy night's event log (50+ events with VLM descriptions) can exceed that. We truncate by recency and priority (pickups and high-confidence events first), but the right answer is a retrieval step that we did not have time to implement.

### Translation (TinyAya): cheaper than you'd think

https://cdn-uploads.huggingface.co/production/uploads/667db115d29e971c591a8031/tgxtr1wWg8CXxWUDs064S.qt
<figcaption><strong>Video 3.</strong> TinyAya translation demo showing local Korean summaries generated from Eyas security events.</figcaption>

TinyAya handles Korean translation of LLM outputs. It runs via llama-cpp-python and caches outputs per source string. In practice, translation is fast (~2–4 seconds per short paragraph) and the quality is good enough for a security summary context.

We only translate LLM-generated text (summary, alert narrative). UI strings are a static i18n table. This distinction matters for performance — you do not want to round-trip every UI label through a GGUF model.

### VoxCPM2 TTS: the fun feature that does not run on CPU

VoxCPM2 produces natural-sounding speech from the event summary. On a machine with CUDA it is genuinely impressive — the audio brief sounds like a calm security system readout.

The problem: it requires CUDA. On HF Spaces CPU tier and on machines without a GPU, we skip TTS gracefully (the Audio Report tab shows an explanatory message). This is the one part of the pipeline that is not truly CPU-friendly, and we knew it going in. The architecture marks TTS as optional throughout; if `torch.cuda.is_available()` is false, the endpoint returns an empty audio object and the UI adapts.

---

## The frontend decision

The hackathon requires a Gradio app. It does not require a Gradio *UI*.

Gradio's `gr.Blocks` lets you expose all pipeline logic as Gradio API endpoints while serving a completely custom frontend as static files. The React frontend communicates with Gradio via `@gradio/client` exactly as the default UI would; from Gradio's perspective nothing is different.

https://cdn-uploads.huggingface.co/production/uploads/667db115d29e971c591a8031/E27q87wFn15LWEDIVrPEX.qt
<figcaption><strong>Video 4.</strong>  Eyas frontend demo. The custom SPA supports multi-camera review with resizable split panels, annotated playback, event timelines, and live pipeline progress.</figcaption>

This was worth doing. The default Gradio UI makes tabbed analysis tools look like form submissions. A proper SPA with resizable split panels, a scatter-chart event timeline, and a live-updating pipeline progress view changes how the tool *feels* to use. Our target users — the people we built this for — understood what the annotated video and event table were within 30 seconds. That would not have happened with a Gradio Dataframe and a Gradio Video component on the same page.

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

## Field test — Joy Convenience Store

We filmed the demo at Joy Convenience Store. It is a close real-world proxy for our target store — similar layout, CCTV setup but a separate business from our teammate's family's shop. It was the first time we ran Eyas on footage from an actual operating store rather than test clips we found online.

Four camera angles were covered: aisle 1, aisle 2, aisle 3, and aisle 4 (the main shopping corridor). We named each clip using the filename convention (`20260615_130000_aisle1.m4v`, etc.) so the zone labels map automatically without any configuration.

**What we learned from running on real footage:**

The pipeline handled the real-world conditions better than expected. Store CCTV is typically high-angle, wide-FOV, compressed H.264 — different from the online footage we had been testing on. YOLO tracked people reliably despite the unconventional angle; the bounding-box padding helped the VLM get enough context from the tighter crops.

The most useful output in the store context turned out to be the per-zone activity count in the Detection Metrics tab. The store operators could immediately see which aisle had the most foot traffic and which periods were quiet. This is the kind of operational question: "how busy was aisle 3 this afternoon?" that does not require a full event narrative to answer.

The event timeline resonated as a communication tool. Showing a scatter chart of timestamped events and then clicking through to a six-second clip for each one made the footage review feel like a triage task rather than a search task. The owner could review a full afternoon session in under three minutes.

Multi-clip analysis (loading all four aisle clips and running them as a batch session) worked as intended — events from each camera are tagged with their zone, and the Summary & Alerts tab produces a unified report across all cameras simultaneously. The per-camera breakdown within the summary helped attribute activity to specific aisles.

One real-world friction point: the store's recording software names clips with a proprietary timestamp format that does not match our `YYYYMMDD_HHMMSS_<zone>` convention. We had to rename the files before upload. This reinforced that a drag-and-drop renaming step or a more flexible filename parser would be a valuable addition.

The demo video was recorded at Joy Convenience Store using these four aisle clips as the input.

---

## Model and tool credits

- [YOLO11n](https://github.com/ultralytics/ultralytics) — Ultralytics
- [MiniCPM-V 4.6](https://huggingface.co/openbmb/MiniCPM-V-4.6) — OpenBMB
- [Nemotron 3 Nano 4B GGUF](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF) — NVIDIA
- [TinyAya](https://huggingface.co/CohereLabs/tiny-aya-global-GGUF) — Cohere Labs
- [VoxCPM2](https://github.com/OpenBMB/VoxCPM) — OpenBMB
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) — Andrei Betlen et al.
- [React](https://react.dev/), [Vite](https://vitejs.dev/), [MUI](https://mui.com/), [Recharts](https://recharts.org/), [Framer Motion](https://www.framer.com/motion/)

---

*Eyas is open source. Space: [build-small-hackathon/eyas](https://huggingface.co/spaces/build-small-hackathon/eyas)*