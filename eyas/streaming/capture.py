"""Live stream capture — RTSP URLs or local webcam via OpenCV."""

import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

try:
    import cv2
    _CV2_OK = True
except ImportError:
    cv2 = None  # type: ignore
    _CV2_OK = False

_CLIPS_DIR = Path(__file__).parent.parent / "data" / "clips"


class StreamCapture:
    """Thread-safe OpenCV video capture.

    Usage::

        cap = StreamCapture()
        cap.start("rtsp://...")   # or cap.start(0) for webcam
        frame = cap.get_rgb()     # H×W×3 uint8 RGB, or None
        path  = cap.start_recording()
        path  = cap.stop_recording()
        cap.stop()
    """

    def __init__(self) -> None:
        self._cap:     Optional[object] = None   # cv2.VideoCapture
        self._thread:  Optional[threading.Thread] = None
        self._writer:  Optional[object] = None   # cv2.VideoWriter
        self._lock     = threading.Lock()
        self.running   = False
        self._latest:  Optional[np.ndarray] = None  # BGR
        self._rec_path: Optional[str] = None

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def start(self, source) -> None:
        """Start capture.  *source* is 0 (webcam) or an RTSP/file URL."""
        if not _CV2_OK:
            raise RuntimeError(
                "opencv-python is not installed. Run: pip install opencv-python"
            )
        if self.running:
            self.stop()
        self._cap    = cv2.VideoCapture(source)
        self.running = True
        self._latest = None
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.running = False
        self.stop_recording()
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None

    def is_open(self) -> bool:
        return self.running and self._cap is not None and self._cap.isOpened()

    # ── Frame access ──────────────────────────────────────────────────────

    def get_rgb(self) -> Optional[np.ndarray]:
        """Latest frame as H×W×3 RGB array, or None if no frame yet."""
        with self._lock:
            frame = self._latest
        if frame is None:
            return None
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def frame_size(self) -> Tuple[int, int]:
        """(width, height) reported by the capture device."""
        if self._cap is not None:
            return (
                int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            )
        return (640, 480)

    def capture_fps(self) -> float:
        if self._cap is not None:
            fps = self._cap.get(cv2.CAP_PROP_FPS)
            return fps if fps > 0 else 25.0
        return 25.0

    # ── Recording ─────────────────────────────────────────────────────────

    def start_recording(self) -> str:
        """Begin writing frames to a timestamped clip.  Returns output path."""
        _CLIPS_DIR.mkdir(parents=True, exist_ok=True)
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = str(_CLIPS_DIR / f"stream_{ts}.mp4")
        w, h = self.frame_size()
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        with self._lock:
            self._writer   = cv2.VideoWriter(path, fourcc, self.capture_fps(), (w, h))
            self._rec_path = path
        return path

    def stop_recording(self) -> Optional[str]:
        """Flush and close the current recording.  Returns saved path or None."""
        with self._lock:
            path, self._rec_path = self._rec_path, None
            writer, self._writer = self._writer, None
        if writer is not None:
            writer.release()
        return path

    @property
    def is_recording(self) -> bool:
        with self._lock:
            return self._writer is not None

    # ── Internal ──────────────────────────────────────────────────────────

    def _loop(self) -> None:
        while self.running:
            cap = self._cap
            if cap is None or not cap.isOpened():
                break
            ok, frame = cap.read()
            if ok:
                with self._lock:
                    self._latest = frame
                    if self._writer is not None:
                        self._writer.write(frame)
            else:
                time.sleep(0.05)


# Module-level singleton shared across UI callbacks
default_capture = StreamCapture()
