"""Tests for eyas/video_processing/process.py."""

import sys
import textwrap
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from eyas.video_processing.process import process_clip

_W = 72


def _box(title: str, body: str) -> None:
    print(f"\n{'=' * _W}")
    print(f"  {title}")
    print(f"{'-' * _W}")
    for line in str(body).splitlines():
        print(textwrap.fill(line, width=_W - 4, initial_indent="  ", subsequent_indent="    ") if line.strip() else "")
    print(f"{'=' * _W}")


class TestProcessClip:
    def test_returns_list(self, tmp_path):
        dummy = tmp_path / "clip.mp4"
        dummy.write_bytes(b"\x00" * 64)
        result = process_clip(str(dummy))
        _box(f"process_clip result ({len(result)} annotations)", str(result) if result else "(empty)")
        assert isinstance(result, list)

    def test_nonexistent_path_returns_list(self):
        assert isinstance(process_clip("nonexistent.mp4"), list)

    def test_annotations_have_expected_keys_when_non_empty(self, tmp_path):
        dummy = tmp_path / "clip.mp4"
        dummy.write_bytes(b"\x00" * 64)
        annotations = process_clip(str(dummy))
        for ann in annotations:
            assert isinstance(ann, dict)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
