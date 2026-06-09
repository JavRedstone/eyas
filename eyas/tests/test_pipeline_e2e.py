    """End-to-end pipeline test: every real component, no stubs.

Flow:
    sample.mp4
        → PersonTracker (YOLO)
        → MiniCPMVLM (real transformers model)
        → EventStructurer
        → Reasoner (GGUF LLM)
        → samples/events.json  +  structured summary

Prerequisites (test is skipped when absent):
    - transformers must be importable (for MiniCPM-V)
    - GGUF model at EYAS_MODEL_PATH env var, or models/nemotron-nano-4b.gguf

Run:
    python tests/test_pipeline_e2e.py
    pytest tests/test_pipeline_e2e.py -v -s
    EYAS_MODEL_PATH=models/mymodel.gguf pytest tests/test_pipeline_e2e.py -v -s
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import cv2
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from object_detection.detector import PersonTracker  # noqa: E402
from video_processing.process import MiniCPMVLM  # noqa: E402
from event_structuring.structurer import EventStructurer, Zone  # noqa: E402
from llm.reasoner import Reasoner  # noqa: E402
from conftest import get_device  # noqa: E402

_SAMPLE = Path(__file__).parent / "samples" / "sample.mp4"
_EVENTS_OUT = Path(__file__).parent / "samples" / "events.json"
_MODEL = Path(os.getenv("EYAS_MODEL_PATH", "models/nemotron-nano-4b.gguf"))

_transformers_available = bool(
    __import__("importlib").util.find_spec("transformers")
)
_model_available = _MODEL.exists()

requires_vlm = pytest.mark.skipif(
    not _transformers_available,
    reason="transformers not installed — MiniCPM-V unavailable",
)
requires_reasoner = pytest.mark.skipif(
    not _model_available,
    reason=f"GGUF model not found at '{_MODEL}'. Set EYAS_MODEL_PATH to enable.",
)


def run_pipeline(video: str = str(_SAMPLE), max_frames: int = 400) -> dict:
    """Run the full pipeline and return a results dict."""
    device = get_device()

    cap = cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 12.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"video {w}x{h} @ {fps:.1f}fps  device={device}")

    tracker = PersonTracker(conf=0.3, device=device)
    vlm = MiniCPMVLM(device=device, dtype="float16", attn="sdpa")
    zones = [Zone(name="shelf_A", bbox=(0, 0, w, h), kind="shelf")]
    structurer = EventStructurer(zones, vlm=vlm, semantic_interval_s=2.0)

    idx = 0
    total_fired = 0
    while cap.isOpened() and idx < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        t = idx / fps
        tracks = tracker.track(frame)
        events = structurer.update(tracks, t, latest_frame=frame)
        for ev in events:
            total_fired += 1
            print(
                f"[{ev.timestamp:.1f}s] track#{ev.track_id} "
                f"@ {ev.zone}: {ev.summary}  (backend={ev.backend})"
            )
        idx += 1
    cap.release()

    structurer.to_json(str(_EVENTS_OUT))

    reasoner = Reasoner(str(_MODEL))
    raw_events = json.loads(_EVENTS_OUT.read_text()) if _EVENTS_OUT.exists() else []
    summary = reasoner.summarize_events(raw_events) if raw_events else {}

    print(f"\nframes processed : {idx}")
    print(f"events fired     : {total_fired}")
    print(f"event log saved  : {_EVENTS_OUT}")
    if summary:
        print(f"risk level       : {summary.get('risk_level')}")
        print(f"summary          : {summary.get('summary', '')[:120]}")

    return {"frames": idx, "events": total_fired, "summary": summary}


# ---------------------------------------------------------------------------
# pytest entry points
# ---------------------------------------------------------------------------

@requires_vlm
def test_frames_are_processed():
    result = run_pipeline()
    assert result["frames"] > 0, "no frames read from sample video"


@requires_vlm
def test_vlm_generates_observations():
    result = run_pipeline()
    assert result["events"] > 0, "real VLM produced zero events"


@requires_vlm
def test_events_json_written():
    run_pipeline()
    assert _EVENTS_OUT.exists()
    data = json.loads(_EVENTS_OUT.read_text())
    assert isinstance(data, list) and len(data) > 0


@requires_vlm
@requires_reasoner
def test_reasoner_produces_valid_summary():
    run_pipeline()
    data = json.loads(_EVENTS_OUT.read_text())
    reasoner = Reasoner(str(_MODEL))
    summary = reasoner.summarize_events(data)
    assert {"summary", "flags", "suspicious_clips", "risk_level"} <= summary.keys()
    assert summary["risk_level"] in {"none", "low", "medium", "high"}
    assert summary["summary"].strip()


# ---------------------------------------------------------------------------
# __main__ (run full pipeline in one shot)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    vid = sys.argv[1] if len(sys.argv) > 1 else str(_SAMPLE)
    result = run_pipeline(vid)
    ok = result["frames"] > 0 and result["events"] > 0
    print("\nE2E PIPELINE TEST PASSED ✅" if ok else "\nE2E PIPELINE TEST FAILED ❌")
    sys.exit(0 if ok else 1)
