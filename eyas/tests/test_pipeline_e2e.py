"""End-to-end pipeline test with a test VLM double and real YOLO tracking.

Flow:
    video -> PersonTracker -> continuous EventStructurer observations
          -> deterministic test observations -> structured event log (JSON)
"""

import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from object_detection.detector import PersonTracker  # noqa: E402
from video_processing.process import PersonObservation  # noqa: E402
from event_structuring.structurer import EventStructurer, Zone  # noqa: E402


def main(video: str, max_frames: int = 400):
    try:
        import torch
        device = "mps" if torch.backends.mps.is_available() else "cpu"
    except Exception:
        device = "cpu"

    cap = cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 12.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"video {w}x{h} @ {fps:.1f}fps device={device}")

    tracker = PersonTracker(conf=0.3, device=device)
    class TestVLM:
        backend = "test"

        def observe_person(self, frames, track_id=None):
            return PersonObservation(
                description="test person",
                activity="standing near a shelf",
                held_objects=[{"name": "test product", "count": 1}],
                pickup_confirmed=True,
                picked_up_items=[{"name": "test product", "count": 1}],
                raw="[TEST]",
                track_id=track_id,
                backend="test",
            )

    vlm = TestVLM()
    # One big 'shelf' zone covering most of the frame so the sample triggers.
    zones = [Zone(name="shelf_A", bbox=(0, 0, w, h), kind="shelf")]
    structurer = EventStructurer(zones, vlm=vlm, semantic_interval_s=1.0)

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
            print(f"[{ev.timestamp:.1f}s] track#{ev.track_id} "
                  f"@ {ev.zone}: {ev.summary}  (backend={ev.backend})")
        idx += 1
    cap.release()

    out = Path(__file__).resolve().parents[1] / "input" / "events.json"
    structurer.to_json(str(out))
    print(f"\nframes processed: {idx}")
    print(f"events fired    : {total_fired}")
    print(f"event log saved : {out}")

    assert idx > 0
    assert total_fired > 0, "no VLM observations were generated"
    assert all(e.summary for e in structurer.events)
    print("\nE2E PIPELINE TEST PASSED ✅")


if __name__ == "__main__":
    vid = sys.argv[1] if len(sys.argv) > 1 else "input/sample.mp4"
    main(vid)
