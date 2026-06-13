# Eyas — Demo Script

Filmed at Joy Convenience Store — our teammate's family's shop and the real-world target this was built for. Four aisle cameras, real footage, no edits.

Target runtime: **3–4 minutes**.

---

## Setup before filming

- App running locally: `python eyas/app.py`
- All four Joy Convenience Store clips pre-renamed and ready to queue:
  - `20260615_130000_aisle1.m4v`
  - `20260615_130000_aisle2.m4v`
  - `20260615_130000_aisle3.m4v`
  - `20260615_130000_aisle4.m4v`
- Models already downloaded (no first-run delay)
- Language set to English

---

## Scene 1 — The problem (~20 s)

Open on the empty left video panel.

> "This is what our teammate's family stares at when something goes missing from the store — hours of footage, no way to know where to start."

Show the splash screen / empty state. Let it breathe for a beat.

---

## Scene 2 — Load footage (~30 s)

Open the footage sidebar.

1. Click the upload zone and select all four aisle clips at once (or drag-and-drop them in).
2. Show the queue: four rows with zone chips — `aisle1`, `aisle2`, `aisle3`, `aisle4` — all checked pending.
3. Briefly point out the zone chip: the filename tells the system which camera each clip came from.
4. Click **Analyze All (4)**.

---

## Scene 3 — Pipeline running (~40 s)

Show the pipeline progress panel as it works through the first clip.

- **Load Video** → **YOLO Tracking** → **VLM Captioning** → **LLM Summary** — step indicators light up in sequence.
- Switch to the left panel and show the annotated video (bounding boxes, track IDs, zone labels) as it appears.

> "YOLO tracks every person frame by frame. The VLM observes each track and describes what they're doing. The LLM reasons over the structured event log."

Let one clip finish and auto-advance to the next. Show the session event counter incrementing in the sidebar.

---

## Scene 4 — Event Timeline (~30 s)

Click the **Event Timeline** tab once all four clips are done.

1. Show the scatter chart: dots spread across zones and timestamps.
2. Click one dot / row in the event table — the six-second clip loads in the left panel and plays.
3. Point out the `zone`, `kind`, and `description` columns.

> "Instead of scrubbing through four hours of video, you see every flagged moment in one chart. Click anything to jump straight to the clip."

---

## Scene 5 — Summary & Alerts (~30 s)

Click the **Summary & Alerts** tab.

1. Show the risk gauge and flag breakdown pie chart at the top (combined across all four cameras).
2. Scroll to the **Per Camera** section — show each aisle's individual summary.
3. Point out the overnight summary text from Nemotron.

> "One report covers all four cameras. Each aisle gets its own breakdown so you know exactly where activity was concentrated."

---

## Scene 6 — Ask Footage (~20 s)

Click the **Ask Footage** tab.

Type (or paste): `Which aisle had the most suspicious activity?`

Show Nemotron's response streaming in. It should name a specific aisle and reference the events.

> "The LLM has read the full event log. Ask it anything about what happened."

---

## Scene 7 — Detection Metrics (~15 s)

Click **Detection Metrics**.

Show the per-zone bar chart and the event density timeline. Point to the busiest aisle bar.

> "For our teammate's family this is an operational tool as much as a security one — which aisle needs more attention, which shift was busiest."

---

## Scene 8 — Language switch (optional, ~15 s)

Click **Settings**, switch to **한국어**, click Save.

Show the UI labels flip to Korean. Play the annotated video — zone labels on the video overlay are now in Korean.

> "Hot-swap to Korean without restarting. Labels in the video, the summary, everything."

---

## Scene 9 — Close (~10 s)

Return to the Event Timeline. Show all four zones populated.

> "Fully offline. No cloud APIs. Runs on a laptop. Every model under 5 billion parameters."

Cut.

---

## Key lines to have ready

| Moment | Line |
|---|---|
| Empty state | "Hours of footage, no way to know where to start." |
| Pipeline running | "Three small models, one chain — detect, observe, reason." |
| Timeline click | "Every flagged moment in one chart. Click to jump to the clip." |
| Per-cam summary | "All four cameras, one report." |
| Ask Footage | "Ask it anything about what happened." |
| Close | "Fully offline. No cloud APIs. Runs on a laptop." |

---

## What to avoid

- Don't wait on first-model-download screens — pre-download everything.
- Don't show the Gradio `/gradio_api` URL or backend ports in the address bar; hide or crop the browser chrome.
- Don't let the demo linger on a processing spinner for more than 10 seconds without narration.
- Don't try to show the Audio Report unless CUDA is available — skip that tab if on CPU only.
