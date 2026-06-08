"""Smoke test: run PersonTracker on the sample video and report tracking stats."""

import sys
from collections import defaultdict
from pathlib import Path

import cv2

# Make the package importable when run from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from object_detection.detector import PersonTracker, crop  # noqa: E402


def main(video: str, max_frames: int = 120):
    # Apple Silicon -> mps; falls back to cpu if unavailable.
    try:
        import torch

        device = "mps" if torch.backends.mps.is_available() else "cpu"
    except Exception:
        device = "cpu"
    print(f"device={device}")

    tracker = PersonTracker(
        weights=str(Path(__file__).parent.parent / "models" / "yolo11n.pt"),
        tracker="botsort.yaml",
        conf=0.4,
        device=device,
    )

    cap = cv2.VideoCapture(video)
    seen_ids = set()
    per_frame_counts = []
    frames_with_people = 0
    sample_crop_shape = None
    idx = 0
    while cap.isOpened() and idx < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        tracks = tracker.track(frame)
        per_frame_counts.append(len(tracks))
        if tracks:
            frames_with_people += 1
            for t in tracks:
                seen_ids.add(t.track_id)
                assert t.label == "person"
                assert len(t.bbox) == 4
            if sample_crop_shape is None:
                sample_crop_shape = crop(frame, tracks[0].bbox, pad=10).shape
        idx += 1
    cap.release()

    print(f"frames processed     : {idx}")
    print(f"frames with people   : {frames_with_people}")
    print(f"unique track IDs seen : {len(seen_ids)} -> {sorted(seen_ids)[:15]}")
    print(f"max people in a frame : {max(per_frame_counts) if per_frame_counts else 0}")
    print(f"sample person crop shape (h,w,c): {sample_crop_shape}")

    # Basic assertions for a smoke test.
    assert idx > 0, "no frames read"
    assert len(seen_ids) > 0, "no persons tracked at all"
    assert sample_crop_shape is not None and sample_crop_shape[0] > 0
    print("\nSMOKE TEST PASSED ✅")


if __name__ == "__main__":
    _default = str(Path(__file__).parent.parent / "input" / "sample.mp4")
    vid = sys.argv[1] if len(sys.argv) > 1 else _default
    main(vid)
