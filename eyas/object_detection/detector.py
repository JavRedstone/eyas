"""Person detection + tracking with YOLOv11 (Ultralytics).

Scope (Eyas visual pipeline):
    YOLO is the *fast spatial layer*. It tracks PEOPLE only and assigns each a
    persistent track ID across frames. It answers: who is in frame, where, and
    when (used downstream to trigger an event). It does NOT do object identity —
    that is MiniCPM-o's job (see video_processing/process.py).

Why person-only:
    Stock YOLO11 weights are COCO-80 and cannot recognise branded retail items
    (chips, coke, etc.). So we don't ask YOLO to read products. YOLO gives us
    stable person tracks; MiniCPM-o reads what each person is holding/took from
    the cropped region around that person.

Usage:
    det = PersonTracker()                      # loads eyas/models/yolo11n.pt (auto-downloads if absent)
    for frame in frames:                       # frame = BGR np.ndarray (cv2)
        tracks = det.track(frame)              # list of Track dicts for this frame

    # or run directly on a video path / RTSP url:
    for frame_idx, tracks in det.track_stream("video.mp4"):
        ...
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

import numpy as np

_MODELS_DIR = Path(__file__).parent.parent / "models"

# COCO class id for 'person'. YOLO11 default weights are COCO-80.
PERSON_CLASS_ID = 0


@dataclass
class Track:
    """A single tracked person detection in one frame."""

    track_id: int
    label: str           # always "person" here
    confidence: float
    bbox: Tuple[int, int, int, int]   # (x1, y1, x2, y2) in pixel coords

    def as_dict(self) -> Dict:
        d = asdict(self)
        d["bbox"] = list(self.bbox)
        return d


def crop(frame: np.ndarray, bbox: Tuple[int, int, int, int], pad: int = 0) -> np.ndarray:
    """Crop a bbox (optionally padded) out of a BGR frame, clamped to bounds."""
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = bbox
    x1 = max(0, x1 - pad)
    y1 = max(0, y1 - pad)
    x2 = min(w, x2 + pad)
    y2 = min(h, y2 + pad)
    return frame[y1:y2, x1:x2]


class PersonTracker:
    """Thin wrapper over Ultralytics YOLO11 `.track()` for person tracking.

    Args:
        weights:  path to model weights. Defaults to eyas/models/yolo11n.pt (nano, fastest).
        tracker:  'botsort.yaml' (default, ReID — survives occlusion, best for
                  CCTV) or 'bytetrack.yaml' (faster, no ReID).
        conf:     confidence threshold.
        device:   None=auto, 'cpu', 'mps' (Apple Silicon), 'cuda', or 0.
    """

    def __init__(
        self,
        weights: str = str(_MODELS_DIR / "yolo11n.pt"),
        tracker: str = "botsort.yaml",
        conf: float = 0.6,
        device: Optional[str] = None,
    ) -> None:
        # Import lazily so importing this module doesn't require ultralytics
        # until a tracker is actually instantiated.
        from ultralytics import YOLO

        self.model = YOLO(weights)
        self.names = self.model.names
        self.tracker = tracker
        self.conf = conf
        self.device = device

    def _parse(self, result) -> List[Track]:
        """Convert one Ultralytics Result into a list of Track objects."""
        tracks: List[Track] = []
        boxes = result.boxes
        if boxes is None or boxes.id is None:
            # No confirmed tracks in this frame yet.
            return tracks
        ids = boxes.id.int().cpu().tolist()
        xyxy = boxes.xyxy.cpu().tolist()
        confs = boxes.conf.cpu().tolist()
        for tid, box, cf in zip(ids, xyxy, confs):
            x1, y1, x2, y2 = (int(round(v)) for v in box)
            tracks.append(
                Track(
                    track_id=int(tid),
                    label="person",
                    confidence=float(cf),
                    bbox=(x1, y1, x2, y2),
                )
            )
        return tracks

    def track(self, frame: np.ndarray) -> List[Track]:
        """Track people in a single frame (BGR np.ndarray).

        Call repeatedly in a loop — persist=True keeps track state across calls.
        """
        results = self.model.track(
            frame,
            persist=True,            # REQUIRED for frame-by-frame loops
            tracker=self.tracker,
            classes=[PERSON_CLASS_ID],
            conf=self.conf,
            device=self.device,
            verbose=False,
        )
        return self._parse(results[0])

    def track_stream(self, source) -> Iterator[Tuple[int, List[Track]]]:
        """Track people across an entire video source.

        Args:
            source: 0 (webcam), a video path, or an RTSP URL.
        Yields:
            (frame_index, [Track, ...]) for each frame.
        """
        stream = self.model.track(
            source=source,
            stream=True,             # generator — low memory
            persist=True,
            tracker=self.tracker,
            classes=[PERSON_CLASS_ID],
            conf=self.conf,
            device=self.device,
            verbose=False,
        )
        for idx, result in enumerate(stream):
            yield idx, self._parse(result)


# Backwards-compatible function kept for the original scaffold API.
# Returns plain dicts so it slots into existing callers.
_default_tracker: Optional[PersonTracker] = None


def detect_objects(frame) -> List[Dict]:
    """Legacy entry point: track people in a single frame, return list of dicts.

    Prefer using PersonTracker directly for new code.
    """
    global _default_tracker
    if _default_tracker is None:
        _default_tracker = PersonTracker()
    return [t.as_dict() for t in _default_tracker.track(frame)]
