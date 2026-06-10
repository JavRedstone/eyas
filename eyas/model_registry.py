"""Background model preloading — starts at app launch, caches instances for fast inference."""
from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

_LOCK = threading.Lock()
_started = False


@dataclass
class ModelState:
    label: str
    icon: str = "hourglass_empty"
    status: str = "waiting"   # waiting | loading | ready | error | skipped
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
        return all(m.status in {"ready", "error", "skipped"} for m in _STATES.values())


def get(key: str) -> Optional[Any]:
    with _LOCK:
        return _INSTANCES.get(key)


def _load_models() -> None:
    from utils.device import get_device
    from utils.paths import models_dir

    device = get_device()

    # ── YOLO ────────────────────────────────────────────────────────────────
    _set("yolo", "sync", "loading")
    try:
        from object_detection.detector import PersonTracker
        tracker = PersonTracker(
            weights=str(models_dir() / "yolo11n.pt"),
            device=device,
        )
        with _LOCK:
            _INSTANCES["yolo"] = tracker
        _set("yolo", "check_circle", "ready")
    except Exception as exc:
        _set("yolo", "error", "error", str(exc)[:100])

    # ── VLM ─────────────────────────────────────────────────────────────────
    _set("vlm", "sync", "loading")
    try:
        from video_processing.process import MiniCPMVLM
        dtype = "float16" if device in {"mps", "cuda"} else "auto"
        vlm = MiniCPMVLM(device=device, dtype=dtype)
        # Load weights during application startup so the first pipeline run
        # does not pay the model-loading cost.
        vlm._ensure_loaded()
        with _LOCK:
            _INSTANCES["vlm"] = vlm
        _set("vlm", "check_circle", "ready")
    except Exception as exc:
        _set("vlm", "error", "error", str(exc)[:100])

    # ── LLM Reasoner ────────────────────────────────────────────────────────
    _set("llm", "sync", "loading")
    try:
        model_path = os.getenv("EYAS_MODEL_PATH", str(models_dir() / "nemotron-nano-4b.gguf"))
        if not os.path.isfile(model_path):
            _set("llm", "warning", "skipped", "GGUF not found — download to enable")
        else:
            from llm.reasoner import Reasoner
            n_gpu_layers = int(os.getenv("EYAS_GPU_LAYERS", "-1"))
            reasoner = Reasoner(model_path, n_gpu_layers=n_gpu_layers)
            reasoner._load_model()
            with _LOCK:
                _INSTANCES["llm"] = reasoner
            _set("llm", "check_circle", "ready")
    except Exception as exc:
        _set("llm", "error", "error", str(exc)[:100])


def start() -> None:
    global _started
    if _started:
        return
    _started = True
    threading.Thread(target=_load_models, daemon=True, name="eyas-model-preloader").start()
