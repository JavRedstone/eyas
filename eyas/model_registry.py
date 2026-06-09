"""Background model preloading — downloads + initialises every model before the splash fades."""
from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

_LOCK = threading.Lock()
_started = False

_NEMOTRON_REPO   = "nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF"
_NEMOTRON_FILE   = "NVIDIA-Nemotron3-Nano-4B-Q4_K_M.gguf"
_VLM_REPO        = "openbmb/MiniCPM-V-4.6"


@dataclass
class ModelState:
    label: str
    icon: str = "hourglass_empty"
    status: str = "waiting"   # waiting | loading | ready | error
    detail: str = ""


_STATES: Dict[str, ModelState] = {
    "yolo": ModelState("Object Detector (YOLO)"),
    "vlm":  ModelState("Visual Language Model"),
    "llm":  ModelState("LLM Reasoner"),
}
_INSTANCES: Dict[str, Any] = {}


def _set(key: str, icon: str, status: str, detail: str = "") -> None:
    with _LOCK:
        _STATES[key].icon = icon
        _STATES[key].status = status
        _STATES[key].detail = detail


def get_states() -> List[ModelState]:
    with _LOCK:
        return [
            ModelState(m.label, m.icon, m.status, m.detail)
            for m in _STATES.values()
        ]


def all_done() -> bool:
    with _LOCK:
        return all(m.status in {"ready", "error"} for m in _STATES.values())


def get(key: str) -> Optional[Any]:
    with _LOCK:
        return _INSTANCES.get(key)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hf_cached(repo_id: str, filename: str = "config.json") -> bool:
    """Return True if the file is already in the local HF cache."""
    try:
        from huggingface_hub import try_to_load_from_cache
        result = try_to_load_from_cache(repo_id, filename)
        return result is not None and result != "None"
    except Exception:
        return False


def _download_gguf(dest: Path) -> None:
    """Download the Nemotron GGUF from HF Hub into models/ and rename to dest."""
    from huggingface_hub import hf_hub_download
    tmp = hf_hub_download(
        repo_id=_NEMOTRON_REPO,
        filename=_NEMOTRON_FILE,
        local_dir=str(dest.parent),
    )
    tmp_path = Path(tmp)
    if tmp_path != dest:
        tmp_path.rename(dest)


# ---------------------------------------------------------------------------
# Sequential model loading (runs in a daemon thread)
# ---------------------------------------------------------------------------

def _load_models() -> None:
    from utils.device import get_device
    from utils.paths import models_dir

    device = get_device()

    # ── YOLO ────────────────────────────────────────────────────────────────
    _set("yolo", "sync", "loading", "Loading weights…")
    try:
        yolo_path = models_dir() / "yolo11n.pt"
        if not yolo_path.is_file():
            _set("yolo", "sync", "loading", "Downloading from Ultralytics…")
        from object_detection.detector import PersonTracker
        tracker = PersonTracker(weights=str(yolo_path), device=device)
        with _LOCK:
            _INSTANCES["yolo"] = tracker
        _set("yolo", "check_circle", "ready", "Ready")
    except Exception as exc:
        _set("yolo", "error", "error", str(exc)[:120])

    # ── VLM ─────────────────────────────────────────────────────────────────
    if _hf_cached(_VLM_REPO):
        _set("vlm", "sync", "loading", "Loading weights…")
    else:
        _set("vlm", "sync", "loading", "Downloading from HuggingFace…")
    try:
        from video_processing.process import MiniCPMVLM
        dtype = "float16" if device in {"mps", "cuda"} else "auto"
        vlm = MiniCPMVLM(device=device, dtype=dtype)
        with _LOCK:
            _INSTANCES["vlm"] = vlm
        _set("vlm", "check_circle", "ready", "Ready")
    except Exception as exc:
        _set("vlm", "error", "error", str(exc)[:120])

    # ── LLM Reasoner ────────────────────────────────────────────────────────
    try:
        gguf_path = Path(os.getenv("EYAS_MODEL_PATH", str(models_dir() / "nemotron-nano-4b.gguf")))

        if gguf_path.is_file():
            _set("llm", "sync", "loading", "Loading weights…")
        else:
            _set("llm", "sync", "loading", "Downloading from HuggingFace…")
            _download_gguf(gguf_path)
            _set("llm", "sync", "loading", "Loading weights…")

        from llm.reasoner import Reasoner
        n_gpu_layers = int(os.getenv("EYAS_GPU_LAYERS", "-1"))
        reasoner = Reasoner(str(gguf_path), n_gpu_layers=n_gpu_layers)
        reasoner._load_model()
        with _LOCK:
            _INSTANCES["llm"] = reasoner
        _set("llm", "check_circle", "ready", "Ready")
    except Exception as exc:
        _set("llm", "error", "error", str(exc)[:120])


def start() -> None:
    global _started
    if _started:
        return
    _started = True
    threading.Thread(target=_load_models, daemon=True, name="eyas-model-preloader").start()
