"""Tests for eyas/video_processing/process.py."""

import sys
import textwrap
import types
from pathlib import Path

import numpy as np
import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from eyas.video_processing.process import LlamaCppMiniCPMVLM, process_clip

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


class TestLlamaCppMiniCPMVLM:
    def test_resolves_official_repository_filename_variants(self, tmp_path):
        actual_model = tmp_path / "MiniCPM-V-4_6-F16.gguf"
        actual_model.write_bytes(b"gguf")
        actual_mmproj = tmp_path / "mmproj-model-f16.gguf"
        actual_mmproj.write_bytes(b"gguf")
        vlm = LlamaCppMiniCPMVLM()

        assert vlm._resolve_local_gguf(
            str(tmp_path / "MiniCPM-V-4.6-F16.gguf"),
            "*MiniCPM*F16.gguf",
            "language model",
        ) == actual_model.resolve()
        assert vlm._resolve_local_gguf(
            str(tmp_path / "mmproj-MiniCPM-V-4.6-F16.gguf"),
            "*mmproj*.gguf",
            "vision projector",
        ) == actual_mmproj.resolve()

    def test_observe_person_uses_multimodal_chat_and_parses_result(
        self, monkeypatch, tmp_path
    ):
        model_path = tmp_path / "minicpmv-f16.gguf"
        model_path.write_bytes(b"gguf")
        mmproj_path = tmp_path / "mmproj-f16.gguf"
        mmproj_path.write_bytes(b"gguf")
        calls = {}

        class FakeLlama:
            def __init__(self, **kwargs):
                calls["load"] = kwargs

            def create_chat_completion(self, **kwargs):
                calls["completion"] = kwargs
                return {
                    "choices": [{
                        "message": {
                            "content": (
                                '{"description":"person in black","activity":'
                                '"picking up a bottle","held_objects":'
                                '[{"name":"bottle","count":1}],'
                                '"pickup_confirmed":true,"picked_up_items":'
                                '[{"name":"bottle","count":1}]}'
                            )
                        }
                    }]
                }

        monkeypatch.setitem(sys.modules, "llama_cpp", types.SimpleNamespace(Llama=FakeLlama))
        class FakeMTMDChatHandler:
            def __init__(self, **kwargs):
                calls["handler"] = kwargs

        monkeypatch.setitem(
            sys.modules,
            "llama_cpp.llama_chat_format",
            types.SimpleNamespace(MTMDChatHandler=FakeMTMDChatHandler),
        )
        vlm = LlamaCppMiniCPMVLM(
            model_path=str(model_path),
            mmproj_path=str(mmproj_path),
            max_image_size=32,
        )
        frames = [np.zeros((48, 64, 3), dtype=np.uint8) for _ in range(3)]

        observation = vlm.observe_person(frames, track_id=7)

        assert calls["load"]["model_path"] == str(model_path.resolve())
        assert calls["handler"]["clip_model_path"] == str(mmproj_path.resolve())
        assert calls["load"]["chat_handler"].__class__ is FakeMTMDChatHandler
        content = calls["completion"]["messages"][0]["content"]
        assert len([part for part in content if part["type"] == "image_url"]) == 3
        labels = [part["text"] for part in content if part["type"] == "text"]
        assert labels[:3] == ["FRAME 1 (oldest)", "FRAME 2", "FRAME 3 (newest)"]
        assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")
        assert calls["completion"]["temperature"] == 0.0
        assert calls["completion"]["top_k"] == 1
        assert calls["completion"]["response_format"] == {"type": "json_object"}
        assert observation.track_id == 7
        assert observation.backend == "llama-cpp-python"
        assert observation.pickup_confirmed is True
        assert observation.picked_up_items == [{"name": "bottle", "count": 1}]

    def test_uses_official_f16_repository_by_default(self, monkeypatch):
        calls = {}

        class FakeLlama:
            @classmethod
            def from_pretrained(cls, **kwargs):
                calls.update(kwargs)
                return cls()

            def create_chat_completion(self, **kwargs):
                return {"choices": [{"message": {"content": '{"pickup_confirmed":false}'}}]}

        monkeypatch.setitem(sys.modules, "llama_cpp", types.SimpleNamespace(Llama=FakeLlama))
        monkeypatch.setitem(
            sys.modules,
            "llama_cpp.llama_chat_format",
            types.SimpleNamespace(MTMDChatHandler=lambda **kwargs: object()),
        )
        monkeypatch.setitem(
            sys.modules,
            "huggingface_hub",
            types.SimpleNamespace(hf_hub_download=lambda **kwargs: __file__),
        )
        vlm = LlamaCppMiniCPMVLM()
        vlm.observe_person([np.zeros((8, 8, 3), dtype=np.uint8)])

        assert calls["repo_id"] == "openbmb/MiniCPM-V-4.6-gguf"
        assert calls["filename"] == "MiniCPM-V-4_6-F16.gguf"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
