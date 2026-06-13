# Project Idea — Offline CCTV Security Assistant (Convenience Store)
Eyas

## 1. Final idea (clean definition)

An offline security review assistant for a single convenience store that converts CCTV footage into a structured, searchable log of events and answers natural-language questions about what happened.

It replaces manual video scrubbing with:
- an event timeline
- short security summaries
- a natural-language query interface over footage history

---

## 2. Core problem it solves

A store owner has CCTV footage but rarely reviews it. When something happens, they waste time scrubbing hours of video to find relevant clips.

Current workflow: manually watch video → slow, inconsistent, tiring.

Target workflow: ask the system and get events + summary instantly.

---

## 3. What the system actually does

### Input
- CCTV video (uploaded clips or RTSP recordings)

### Processing pipeline

**Stage 1 — Vision (MiniCPM-V):**
- detect people and motion
- process short clips
- extract candidate events

**Stage 2 — Event structuring (CV logic):**
- define zones (entrance, counter, back door)
- track movement and dwell time
- convert raw detections into events

Example event (JSON):

```json
{
  "type": "after_hours_entry",
  "time": "02:14:22",
  "duration": 38,
  "zone": "back_door"
}
```

**Stage 3 — Language reasoning (small LLM):**
- summarize event logs
- answer questions about footage history
- generate short security reports

Suggested models:
- MiniCPM5-1B or Tiny Aya 3.3B for text reasoning
- MiniCPM-V (video/vision) for detection
- Optional: Nemotron 4B if stronger reasoning is required

---

## 4. Outputs

### Timeline view
- timestamped events
- zone-based actions
- entry/exit and dwell events

### Security summary
- e.g. “No incidents detected overnight”
- e.g. “1 after-hours entry, consistent with delivery pattern”

### Query interface
- natural questions: “Anything unusual overnight?”
- focused queries: “Show back door activity” or “What happened between 2–4 AM?”

---

## 5. Key design principle

Video is not the product — the event log is. The UI's focus is fast, verifiable answers backed by short clips.

---

## 6. Why this is good for Backyard AI
- Real user: a single convenience store owner
- Real workflow: routine CCTV review and incident lookup
- Clear time savings: 30–60 minutes → ~2 minutes per investigation
- Offline-first: can run without cloud APIs (bonus eligibility)
- Demo-friendly: Gradio timeline + chat + clip playback

---

## 7. Model plan (allowed stack)
- Vision / video understanding: MiniCPM-V (or equivalent small VLM)
- Text reasoning: MiniCPM5-1B (fast baseline) or Tiny Aya 3.3B (higher quality)
- Optional upgrade: Nemotron 4B for stronger reasoning if needed

---

## 8. What makes it stand out
Not just object detection or surveillance UI — this turns hours of footage into a searchable security report system tailored to one business.

---

## 9. MVP scope (48–72 hours)

### Must-have
- video upload (or provided sample CCTV)
- person detection and simple tracking
- zone rules (door / entrance / counter)
- event log generation and JSON store (or SQLite)
- timeline UI in Gradio with clip previews
- "ask footage" chat that queries the event log
- codex commits / traces 

### Nice-to-have
- VLM explanations for selected clips
- anomaly flagging ("review recommended")
- auto-generated daily report button

### Skip for MVP
- facial recognition
- full real-time streaming
- inventory/floorplan integrations
- complex multi-camera synchronization

---

## 10. Build plan (48–72 hours)

### Phase 1 — Core CV pipeline
- ingest video and split into short clips
- run MiniCPM-V on clips to detect people and motion
- generate raw detection records

### Phase 2 — Event system
- define zones and simple heuristics
- convert detections into a structured event log
- persist events in JSON or SQLite

### Phase 3 — LLM layer
- implement summarization and Q&A over the event log
- add simple prompt templates and few-shot examples

### Phase 4 — Gradio app
- timeline viewer with timestamped events
- clip preview player
- chat-style query box that responds from the log

### Phase 5 — Polish and demo
- add "overnight report" export
- clean UI narrative and labels
- record a short demo video showing pain → fix → metric

---

## 11. Final positioning statement (for submission)

An offline CCTV intelligence system that turns hours of convenience store footage into a structured security log and natural-language report, allowing owners to review an entire day of activity in minutes without watching video.

---

## 12. What shipped (vs. plan)

Everything in the MVP must-have list shipped. Notable additions beyond the MVP scope:

- **Full multi-model chain**: YOLO11n → MiniCPM-V 4.6 → heuristic structurer → Nemotron 3 Nano 4B → TinyAya translation → VoxCPM2 TTS
- **Custom React SPA**: replaced Gradio UI entirely; resizable split panels, scatter-chart timeline, animated splash screen, drag-handle sidebar
- **Multi-camera session**: batch-process multiple clips and produce a unified cross-camera summary with per-zone breakdowns
- **Bilingual support**: English / Korean hot-swap without restart; Korean overlay labels on annotated video
- **Field tested**: demo filmed at Joy Convenience Store on four real aisle cameras; the store owner reviewed their own footage using the system

Skipped (as planned): facial recognition, real-time streaming, inventory integrations, complex multi-camera synchronization.
