"""Module test: YOLO + real MiniCPM-V — validates the full VLM observation path.

Run:
    python tests/test_module_vlm.py
    pytest tests/test_module_vlm.py -v -s
"""

import sys
import time
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from object_detection.detector import PersonTracker, crop  # noqa: E402
from video_processing.buffer import sample_frames  # noqa: E402
from video_processing.process import MiniCPMVLM  # noqa: E402
from utils.device import get_device  # noqa: E402


_SAMPLE = Path(__file__).parent.parent / "samples" / "sample.mp4"


def collect_person_crops(video: str, device: str, max_frames: int = 120, k: int = 6):
    tracker = PersonTracker(conf=0.3, device=device)
    cap = cv2.VideoCapture(video)
    crops = []
    idx = 0
    while cap.isOpened() and idx < max_frames and len(crops) < 30:
        ok, frame = cap.read()
        if not ok:
            break
        tracks = tracker.track(frame)
        if tracks:
            c = crop(frame, tracks[0].bbox, pad=20)
            if c.size > 0:
                crops.append(c)
        idx += 1
    cap.release()
    return sample_frames(crops, k=k)


def main(video: str = str(_SAMPLE)):
    device = get_device()
    print(f"device={device}")

    crops = collect_person_crops(video, device)
    print(f"collected {len(crops)} person crops, shapes={[c.shape for c in crops][:3]}...")
    assert crops, "no person crops collected"

    print("loading MiniCPM-V 4.6 (1.3B)... (first run downloads ~3GB)")
    t0 = time.time()
    vlm = MiniCPMVLM(device=device, dtype="float16", attn="sdpa")
    ann = vlm.caption_frames(crops, max_new_tokens=128)
    observation = vlm.observe_person(crops[-2:], max_new_tokens=160)
    dt = time.time() - t0

    print(f"\nbackend  : {ann.backend}")
    print(f"latency  : {dt:.1f}s (incl. model load)")
    print(f"caption  :\n{ann.caption}")
    print(f"items    : {ann.items}")
    print(f"summary  : {ann.summary()}")
    print(f"description : {observation.description}")
    print(f"activity    : {observation.activity}")
    print(f"held objects     : {observation.held_objects}")
    print(f"pickup confirmed : {observation.pickup_confirmed}")
    print(f"picked up items  : {observation.picked_up_items}")

    assert ann.backend == "minicpmv", "did not use the real model"
    assert isinstance(ann.caption, str) and len(ann.caption) > 0
    assert observation.backend == "minicpmv"
    assert observation.description or observation.activity
    print("\nVLM MODULE TEST PASSED ✅")


if __name__ == "__main__":
    vid = sys.argv[1] if len(sys.argv) > 1 else str(_SAMPLE)
    main(vid)
