"""Placeholder object detection interface.

Implement a lightweight wrapper around YOLO or similar.
Functions should be synchronous and accept a frame or path, returning detections.
"""

from typing import List, Dict


def detect_objects(frame) -> List[Dict]:
    """Run object detection on a single frame.
    Returns a list of detections with keys: label, confidence, bbox
    """
    # TODO: wire a real model here
    return []
