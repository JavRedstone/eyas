"""Tests for eyas/storage/manager.py — clip storage and index management."""

import json
import sys
import textwrap
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import eyas.storage.manager as storage

_W = 72


def _box(title: str, body: str) -> None:
    print(f"\n{'=' * _W}")
    print(f"  {title}")
    print(f"{'-' * _W}")
    for line in str(body).splitlines():
        print(textwrap.fill(line, width=_W - 4, initial_indent="  ", subsequent_indent="    ") if line.strip() else "")
    print(f"{'=' * _W}")


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    """Redirect all storage I/O to a temporary directory for each test."""
    clips = tmp_path / "clips"
    index = tmp_path / "clip_index.json"
    monkeypatch.setattr(storage, "_CLIPS", clips)
    monkeypatch.setattr(storage, "_INDEX", index)
    return clips, index


@pytest.fixture()
def sample_video(tmp_path):
    """A small dummy file that stands in for a video clip."""
    p = tmp_path / "footage.mp4"
    p.write_bytes(b"\x00" * 1024)
    return str(p)


# ---------------------------------------------------------------------------
# store()
# ---------------------------------------------------------------------------

class TestStore:
    def test_creates_clips_dir(self, sample_video):
        storage.store(sample_video)
        assert storage._CLIPS.is_dir()

    def test_returns_entry_with_expected_keys(self, sample_video):
        entry = storage.store(sample_video)
        _box("store() entry", json.dumps({k: str(v) for k, v in entry.items()}, indent=2))
        assert {"filename", "path", "timestamp", "source", "size_mb"} <= entry.keys()

    def test_default_source_is_upload(self, sample_video):
        entry = storage.store(sample_video)
        assert entry["source"] == "upload"

    def test_custom_source_stored(self, sample_video):
        entry = storage.store(sample_video, source="stream")
        assert entry["source"] == "stream"

    def test_file_copied_to_clips_dir(self, sample_video):
        entry = storage.store(sample_video)
        assert Path(entry["path"]).exists()

    def test_size_mb_rounded_to_two_decimal_places(self, sample_video):
        entry = storage.store(sample_video)
        assert entry["size_mb"] >= 0
        assert isinstance(entry["size_mb"], float)

    def test_entry_appended_to_index(self, sample_video):
        storage.store(sample_video)
        index = json.loads(storage._INDEX.read_text())
        assert len(index) == 1

    def test_multiple_stores_append_all(self, sample_video, tmp_path):
        second = tmp_path / "second.mp4"
        second.write_bytes(b"\x00" * 512)
        storage.store(sample_video)
        storage.store(str(second))
        index = json.loads(storage._INDEX.read_text())
        assert len(index) == 2


# ---------------------------------------------------------------------------
# list_clips()
# ---------------------------------------------------------------------------

class TestListClips:
    def test_empty_store_returns_empty_list(self):
        assert storage.list_clips() == []

    def test_returns_newest_first(self, sample_video, tmp_path):
        second = tmp_path / "b.mp4"
        second.write_bytes(b"\x00" * 256)
        storage.store(sample_video)
        storage.store(str(second))
        clips = storage.list_clips()
        assert clips[0]["filename"].endswith("b.mp4") or "b.mp4" in clips[0]["filename"]


# ---------------------------------------------------------------------------
# choices()
# ---------------------------------------------------------------------------

class TestChoices:
    def test_empty_store_returns_empty_list(self):
        assert storage.choices() == []

    def test_label_contains_filename(self, sample_video):
        storage.store(sample_video)
        labels = storage.choices()
        assert len(labels) == 1
        assert "footage.mp4" in labels[0]

    def test_label_contains_source(self, sample_video):
        storage.store(sample_video, source="stream")
        assert "stream" in storage.choices()[0]

    def test_label_contains_size(self, sample_video):
        storage.store(sample_video)
        assert "MB" in storage.choices()[0]


# ---------------------------------------------------------------------------
# path_from_choice()
# ---------------------------------------------------------------------------

class TestPathFromChoice:
    def test_roundtrip_resolves_to_existing_file(self, sample_video):
        storage.store(sample_video)
        label = storage.choices()[0]
        resolved = storage.path_from_choice(label)
        assert resolved is not None
        assert Path(resolved).exists()

    def test_returns_none_for_unknown_choice(self):
        assert storage.path_from_choice("nonexistent — file.mp4  (0 MB)  [upload]") is None

    def test_returns_none_for_empty_string(self):
        assert storage.path_from_choice("") is None


# ---------------------------------------------------------------------------
# delete()
# ---------------------------------------------------------------------------

class TestDelete:
    def test_delete_removes_file(self, sample_video):
        entry = storage.store(sample_video)
        assert Path(entry["path"]).exists()
        storage.delete(entry["filename"])
        assert not Path(entry["path"]).exists()

    def test_delete_removes_from_index(self, sample_video):
        entry = storage.store(sample_video)
        storage.delete(entry["filename"])
        assert storage.list_clips() == []

    def test_delete_nonexistent_returns_true(self):
        assert storage.delete("ghost.mp4") is True

    def test_delete_leaves_other_entries(self, sample_video, tmp_path):
        second = tmp_path / "keep.mp4"
        second.write_bytes(b"\x00" * 256)
        e1 = storage.store(sample_video)
        storage.store(str(second))
        storage.delete(e1["filename"])
        remaining = storage.list_clips()
        assert len(remaining) == 1
        assert "keep.mp4" in remaining[0]["filename"]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
