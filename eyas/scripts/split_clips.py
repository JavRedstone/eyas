"""Utility: split a long video into fixed-length short clips.

Used for offline batch processing of uploaded footage (the non-realtime path):
chop a long recording into clip_len-second segments that can be analysed one by
one. Uses OpenCV so there is no hard ffmpeg dependency, though ffmpeg is faster
if available.
"""

from __future__ import annotations

import os
from typing import List

import cv2


def split_video(path: str, clip_len: int = 10, out_dir: str | None = None) -> List[str]:
    """Split `path` into clip_len-second .mp4 segments.

    Args:
        path:     source video.
        clip_len: segment length in seconds.
        out_dir:  output directory (default: alongside source in a 'clips' dir).
    Returns:
        list of written clip file paths, in order.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    if out_dir is None:
        base = os.path.splitext(os.path.basename(path))[0]
        out_dir = os.path.join(os.path.dirname(os.path.abspath(path)), f"{base}_clips")
    os.makedirs(out_dir, exist_ok=True)

    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frames_per_clip = max(1, int(round(fps * clip_len)))
    fourcc = cv2.VideoWriter_fourcc(*"avc1")

    paths: List[str] = []
    writer = None
    clip_idx = 0
    frame_idx = 0
    try:
        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                break
            if frame_idx % frames_per_clip == 0:
                if writer is not None:
                    writer.release()
                clip_path = os.path.join(out_dir, f"clip_{clip_idx:04d}.mp4")
                writer = cv2.VideoWriter(clip_path, fourcc, fps, (w, h))
                paths.append(clip_path)
                clip_idx += 1
            writer.write(frame)
            frame_idx += 1
    finally:
        if writer is not None:
            writer.release()
        cap.release()
    return paths


if __name__ == "__main__":
    import sys

    src = sys.argv[1] if len(sys.argv) > 1 else "../input/sample.mp4"
    clips = split_video(src, clip_len=10)
    print(f"wrote {len(clips)} clips:")
    for p in clips:
        print(" ", p)
