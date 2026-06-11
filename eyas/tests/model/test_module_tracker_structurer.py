"""Module test: YOLO PersonTracker + EventStructurer with a stub VLM.

The VLM is replaced by a deterministic test double so this test runs fast
and without any model weights.  It validates that the tracker → structurer
boundary works correctly: detections are turned into timed observations and
the structurer emits at least one event for a video containing people.

Run:
    python tests/test_module_tracker_structurer.py
    pytest tests/test_module_tracker_structurer.py -v -s
"""

import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from object_detection.detector import PersonTracker  # noqa: E402
from video_processing.process import PersonObservation  # noqa: E402
from event_structuring.structurer import EventStructurer, Zone  # noqa: E402
from utils.device import get_device  # noqa: E402
from utils.video import get_video_info  # noqa: E402


_SAMPLE = Path(__file__).parent.parent / "samples" / "sample.mp4"
_EVENTS_OUT = Path(__file__).parent.parent / "samples" / "events.json"


class _StubVLM:
    """Deterministic stand-in — always confirms a pickup of 'test product'."""
    backend = "stub"

    def observe_person(self, frames, track_id=None):
        return PersonObservation(
            description="test person",
            activity="standing near a shelf",
            held_objects=[{"name": "test product", "count": 1}],
            pickup_confirmed=True,
            picked_up_items=[{"name": "test product", "count": 1}],
            raw="[STUB]",
            track_id=track_id,
            backend="stub",
        )


def main(video: str = str(_SAMPLE), max_frames: int = 400):
    device = get_device()

    cap = cv2.VideoCapture(video)
    fps, w, h = get_video_info(cap)
    print(f"video {w}x{h} @ {fps:.1f}fps  device={device}")

    tracker = PersonTracker(conf=0.3, device=device)
    zones = [Zone(name="shelf_A", bbox=(0, 0, w, h), kind="shelf")]
    structurer = EventStructurer(zones, vlm=_StubVLM(), semantic_interval_s=1.0)

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
    print(f"\nframes processed : {idx}")
    print(f"events fired     : {total_fired}")
    print(f"event log saved  : {_EVENTS_OUT}")

    assert idx > 0, "no frames read from sample video"
    assert total_fired > 0, "no VLM observations were generated"
    assert all(e.summary for e in structurer.events)
    print("\nTRACKER + STRUCTURER MODULE TEST PASSED ✅")


if __name__ == "__main__":
    vid = sys.argv[1] if len(sys.argv) > 1 else str(_SAMPLE)
    main(vid)
