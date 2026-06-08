"""Tests for eyas/streaming/capture.py — StreamCapture lifecycle and properties."""

import sys
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

_REPO_ROOT = Path(__file__).parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import numpy as np
import pytest

from eyas.streaming.capture import StreamCapture

_W = 72


def _box(title: str, body: str) -> None:
    print(f"\n{'=' * _W}")
    print(f"  {title}")
    print(f"{'-' * _W}")
    for line in str(body).splitlines():
        print(textwrap.fill(line, width=_W - 4, initial_indent="  ", subsequent_indent="    ") if line.strip() else "")
    print(f"{'=' * _W}")


@pytest.fixture()
def cap():
    return StreamCapture()


# ---------------------------------------------------------------------------
# Initial state (no start() called)
# ---------------------------------------------------------------------------

class TestInitialState:
    def test_not_running(self, cap):
        _box(
            "StreamCapture initial state",
            f"running={cap.running}\n"
            f"is_open={cap.is_open()}\n"
            f"frame_size={cap.frame_size()}\n"
            f"capture_fps={cap.capture_fps()}",
        )
        assert not cap.running

    def test_is_open_false(self, cap):
        assert not cap.is_open()

    def test_get_rgb_returns_none(self, cap):
        assert cap.get_rgb() is None

    def test_not_recording(self, cap):
        assert not cap.is_recording

    def test_stop_recording_returns_none(self, cap):
        assert cap.stop_recording() is None

    def test_frame_size_default(self, cap):
        assert cap.frame_size() == (640, 480)

    def test_capture_fps_default(self, cap):
        assert cap.capture_fps() == 25.0


# ---------------------------------------------------------------------------
# start() with a mocked cv2.VideoCapture
# ---------------------------------------------------------------------------

class TestStartStop:
    def _make_mock_cap(self, width=1280, height=720, fps=30.0):
        mock_vc = MagicMock()
        mock_vc.isOpened.return_value = True
        mock_vc.read.return_value = (True, np.zeros((720, 1280, 3), dtype=np.uint8))
        mock_vc.get.side_effect = lambda prop: {
            0: width,   # CAP_PROP_FRAME_WIDTH
            1: height,  # CAP_PROP_FRAME_HEIGHT
            5: fps,     # CAP_PROP_FPS
        }.get(prop, 0)
        return mock_vc

    def test_start_sets_running(self):
        mock_vc = self._make_mock_cap()
        with patch("eyas.streaming.capture.cv2") as mock_cv2:
            mock_cv2.VideoCapture.return_value = mock_vc
            cap = StreamCapture()
            cap.start(0)
            assert cap.running
            cap.stop()

    def test_stop_clears_running(self):
        mock_vc = self._make_mock_cap()
        with patch("eyas.streaming.capture.cv2") as mock_cv2:
            mock_cv2.VideoCapture.return_value = mock_vc
            cap = StreamCapture()
            cap.start(0)
            cap.stop()
            assert not cap.running

    def test_frame_size_from_capture(self):
        mock_vc = self._make_mock_cap(width=1920, height=1080)
        with patch("eyas.streaming.capture.cv2") as mock_cv2:
            mock_cv2.CAP_PROP_FRAME_WIDTH = 0
            mock_cv2.CAP_PROP_FRAME_HEIGHT = 1
            mock_cv2.VideoCapture.return_value = mock_vc
            cap = StreamCapture()
            cap._cap = mock_vc
            assert cap.frame_size() == (1920, 1080)

    def test_capture_fps_from_capture(self):
        mock_vc = self._make_mock_cap(fps=60.0)
        with patch("eyas.streaming.capture.cv2") as mock_cv2:
            mock_cv2.CAP_PROP_FPS = 5
            mock_vc.get.return_value = 60.0
            cap = StreamCapture()
            cap._cap = mock_vc
            assert cap.capture_fps() == 60.0


# ---------------------------------------------------------------------------
# Recording
# ---------------------------------------------------------------------------

class TestRecording:
    def test_start_recording_sets_is_recording(self, tmp_path):
        mock_vc = MagicMock()
        mock_vc.isOpened.return_value = True
        mock_vc.get.return_value = 30.0

        mock_writer = MagicMock()

        with patch("eyas.streaming.capture.cv2") as mock_cv2, \
             patch("eyas.streaming.capture._CLIPS_DIR", tmp_path):
            mock_cv2.VideoCapture.return_value = mock_vc
            mock_cv2.VideoWriter.return_value = mock_writer
            mock_cv2.VideoWriter_fourcc.return_value = 0x58564944
            mock_cv2.CAP_PROP_FRAME_WIDTH  = 0
            mock_cv2.CAP_PROP_FRAME_HEIGHT = 1
            mock_cv2.CAP_PROP_FPS = 5
            mock_vc.get.side_effect = lambda p: {0: 640, 1: 480, 5: 30.0}.get(p, 30.0)

            cap = StreamCapture()
            cap._cap = mock_vc
            cap.running = True
            cap.start_recording()
            assert cap.is_recording

    def test_stop_recording_clears_is_recording(self, tmp_path):
        mock_vc = MagicMock()
        mock_vc.isOpened.return_value = True
        mock_vc.get.return_value = 30.0
        mock_writer = MagicMock()

        with patch("eyas.streaming.capture.cv2") as mock_cv2, \
             patch("eyas.streaming.capture._CLIPS_DIR", tmp_path):
            mock_cv2.VideoCapture.return_value = mock_vc
            mock_cv2.VideoWriter.return_value = mock_writer
            mock_cv2.VideoWriter_fourcc.return_value = 0x58564944
            mock_cv2.CAP_PROP_FRAME_WIDTH  = 0
            mock_cv2.CAP_PROP_FRAME_HEIGHT = 1
            mock_cv2.CAP_PROP_FPS = 5
            mock_vc.get.side_effect = lambda p: {0: 640, 1: 480, 5: 30.0}.get(p, 30.0)

            cap = StreamCapture()
            cap._cap = mock_vc
            cap.running = True
            cap.start_recording()
            path = cap.stop_recording()
            assert not cap.is_recording
            assert path is not None


# ---------------------------------------------------------------------------
# Missing cv2
# ---------------------------------------------------------------------------

class TestMissingCv2:
    def test_start_raises_when_cv2_missing(self):
        with patch("eyas.streaming.capture._CV2_OK", False):
            cap = StreamCapture()
            with pytest.raises(RuntimeError, match="opencv"):
                cap.start(0)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
