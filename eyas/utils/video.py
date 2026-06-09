"""Video I/O helpers: capture metadata and writer construction."""

from __future__ import annotations

from typing import Tuple

import cv2


def get_video_info(cap: cv2.VideoCapture) -> Tuple[float, int, int]:
    """Return (fps, width, height) from an open VideoCapture."""
    fps = cap.get(cv2.CAP_PROP_FPS) or 12.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    return fps, width, height


def create_video_writer(
    path: str, fps: float, width: int, height: int
) -> cv2.VideoWriter:
    """Create an mp4v VideoWriter for the given path and dimensions."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    return cv2.VideoWriter(path, fourcc, fps, (width, height))
