"""Tests for eyas/object_detection/detector.py."""

import numpy as np

from eyas.object_detection.detector import detect_objects


class TestDetectObjects:
    def test_returns_list(self):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        assert isinstance(detect_objects(frame), list)

    def test_none_frame_returns_list(self):
        assert isinstance(detect_objects(None), list)

    def test_detections_have_expected_keys_when_non_empty(self):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        detections = detect_objects(frame)
        for det in detections:
            assert {"label", "confidence", "bbox"} <= det.keys()
