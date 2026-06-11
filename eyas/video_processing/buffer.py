"""Rolling frame buffer + clip extraction for event-triggered VLM analysis.

Why this exists:
    MiniCPM-o is too slow to run on every frame. Instead, YOLO tracks people in
    real time and fires an *event* (e.g. a person lingers at a shelf zone). When
    that happens we need the few seconds of video *around* that moment to feed
    the VLM — not a single frame, because "taking an item" is an action that
    only reads correctly across multiple frames.

    FrameRingBuffer keeps the last N seconds of frames in memory so that, at the
    instant an event triggers, we can pull a short clip ending (or centred) on
    that moment without having re-read the whole video.

Two helpers:
    FrameRingBuffer       — in-memory rolling window of recent frames.
    write_clip            — dump a list of frames to an .mp4 on disk (for VLM
                            paths that take a file) or keep them in memory.
    sample_frames         — evenly downsample a frame list to K frames (VLMs
                            want a handful of frames, not 100s).
"""

from __future__ import annotations

import os
from collections import deque
from dataclasses import dataclass
from typing import Deque, List, Optional, Tuple

import cv2
import numpy as np


@dataclass
class Stamped:
    """A frame tagged with its source frame index and timestamp (seconds)."""

    index: int
    t: float
    frame: np.ndarray


class FrameRingBuffer:
    """Fixed-duration rolling buffer of recent frames.

    Args:
        fps:            source frame rate (used to size the window and to write
                        clips at the right speed).
        seconds:        how many seconds of history to retain.
    """

    def __init__(self, fps: float, seconds: float = 6.0) -> None:
        self.fps = max(1.0, float(fps))
        self.seconds = float(seconds)
        self.maxlen = max(1, int(round(self.fps * self.seconds)))
        self._buf: Deque[Stamped] = deque(maxlen=self.maxlen)

    def push(self, frame: np.ndarray, index: int, t: Optional[float] = None) -> None:
        """Add a frame. `t` defaults to index / fps if not supplied."""
        if t is None:
            t = index / self.fps
        self._buf.append(Stamped(index=index, t=t, frame=frame))

    def __len__(self) -> int:
        return len(self._buf)

    def window(self, seconds: Optional[float] = None) -> List[Stamped]:
        """Return the most recent `seconds` of frames (default: whole buffer)."""
        items = list(self._buf)
        if seconds is None:
            return items
        if not items:
            return items
        cutoff = items[-1].t - seconds
        return [s for s in items if s.t >= cutoff]

    def frames(self, seconds: Optional[float] = None) -> List[np.ndarray]:
        """Convenience: just the raw frames in the recent window."""
        return [s.frame for s in self.window(seconds)]

    def time_span(self) -> Tuple[float, float]:
        """(start_t, end_t) of buffered frames, or (0, 0) if empty."""
        if not self._buf:
            return (0.0, 0.0)
        return (self._buf[0].t, self._buf[-1].t)


def sample_frames(frames: List[np.ndarray], k: int = 8) -> List[np.ndarray]:
    """Evenly downsample a frame list to at most k frames (keeps temporal order).

    VLMs want a small handful of frames spanning the action, not every frame.
    """
    n = len(frames)
    if n == 0:
        return []
    if n <= k:
        return list(frames)
    idxs = np.linspace(0, n - 1, k).round().astype(int)
    return [frames[i] for i in idxs]


def write_clip(frames: List[np.ndarray], path: str, fps: float = 12.0) -> str:
    """Write frames (BGR np.ndarrays) to an .mp4 file. Returns the path.

    Used when a VLM path expects a file rather than in-memory frames.
    """
    if not frames:
        raise ValueError("no frames to write")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    h, w = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"avc1")
    writer = cv2.VideoWriter(path, fourcc, fps, (w, h))
    try:
        for f in frames:
            # Guard against frames of differing size (e.g. crops); resize to first.
            if f.shape[:2] != (h, w):
                f = cv2.resize(f, (w, h))
            writer.write(f)
    finally:
        writer.release()
    return path
