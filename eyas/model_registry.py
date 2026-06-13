"""Background model preloading — downloads + initialises every model before the splash fades."""
from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

_LOCK = threading.Lock()
_started = False

_VLM_REPO        = "openbmb/MiniCPM-V-4.6"
_TTS_REPO        = "openbmb/VoxCPM2"


@dataclass
class ModelState:
    label: str
    model_name: str = ""
    icon: str = "hourglass_empty"
    status: str = "waiting"   # waiting | loading | ready | error
    detail: str = ""


_STATES: Dict[str, ModelState] = {
    "yolo":    ModelState("Object Detector",   "YOLO11n"),
    "vlm":     ModelState("Vision Analyzer",   "MiniCPM-V 4.6"),
    "llm":     ModelState("LLM Reasoner",      "Nemotron-Nano-4B"),
    "tts":     ModelState("Text-to-Speech",    "VoxCPM2", icon="touch_app", status="on_demand"),
    "tinyaya": ModelState("Translator",        "Tiny Aya Global"),
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
            ModelState(m.label, m.model_name, m.icon, m.status, m.detail)
            for m in _STATES.values()
        ]


def all_done() -> bool:
    with _LOCK:
        return all(m.status in {"ready", "error", "on_demand"} for m in _STATES.values())


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
        vlm = MiniCPMVLM(
            device=device,
            dtype=dtype,
            max_image_size=672,
            max_new_tokens=256,
        )
        # Load weights during application startup so the first pipeline run
        # does not pay the model-loading cost.
        vlm._ensure_loaded()
        with _LOCK:
            _INSTANCES["vlm"] = vlm
        if hasattr(vlm, "_ensure_loaded"):
            vlm._ensure_loaded()
        _set("vlm", "check_circle", "ready", "Ready")
    except Exception as exc:
        _set("vlm", "error", "error", str(exc)[:120])

    # ── LLM Reasoner (Nemotron GGUF) ─────────────────────────────────────────
    from llm.reasoner import Reasoner as _GGUFReasoner
    _nemotron_file = models_dir() / "nemotron-nano-4b.gguf"
    with _LOCK:
        _STATES["llm"].model_name = "Nemotron-Nano-4B"
    _set("llm", "sync", "loading",
         "Loading weights…" if _nemotron_file.is_file() else "Downloading from HuggingFace…")
    try:
        n_gpu_layers = int(os.getenv("EYAS_GPU_LAYERS", "-1"))
        reasoner = _GGUFReasoner(str(_nemotron_file), n_gpu_layers=n_gpu_layers)
        reasoner._load_model()
        with _LOCK:
            _INSTANCES["llm"] = reasoner
        _set("llm", "check_circle", "ready", "Ready")
    except Exception as exc:
        import traceback
        traceback.print_exc()
        _set("llm", "error", "error", str(exc)[:120])

    # TTS (VoxCPM2) is intentionally NOT pre-loaded here.
    # It loads on demand via load_tts_on_demand() so the VLM can be offloaded first.

    # ── Tiny Aya (translation) ───────────────────────────────────────────────
    from postprocessing import TINYAYA_GGUF_REPO, TINYAYA_GGUF_FILE
    _set("tinyaya", "sync", "loading",
         "Loading weights…" if _hf_cached(TINYAYA_GGUF_REPO, TINYAYA_GGUF_FILE) else "Downloading…")
    try:
        from postprocessing import get_tinyaya_model
        use_gpu = device in {"mps", "cuda"}
        model = get_tinyaya_model(use_gpu=use_gpu)
        with _LOCK:
            _INSTANCES["tinyaya"] = model
        _set("tinyaya", "check_circle", "ready", "Ready")
    except Exception as exc:
        _set("tinyaya", "error", "error", str(exc)[:120])


def offload_vlm() -> None:
    """Move the VLM off GPU to free VRAM. Safe to call at any time; no-op if already on CPU or not loaded."""
    vlm = get("vlm")
    if vlm is not None and hasattr(vlm, "offload"):
        vlm.offload()


def offload_llm() -> None:
    """Delete the llama.cpp Llama object to free Metal GPU memory.
    The LLM reloads from disk on the next summarize call."""
    llm = get("llm")
    if llm is not None and hasattr(llm, "offload"):
        llm.offload()


def load_tts_on_demand() -> Optional[Any]:
    """Lazily load TTS, offloading VLM + LLM first so there is enough VRAM.
    Returns the TTS model instance, or None on failure."""
    with _LOCK:
        existing = _INSTANCES.get("tts")
    if existing is not None:
        return existing

    # Free both PyTorch MPS (VLM) and llama.cpp Metal (LLM) allocations before
    # loading the TTS model.
    offload_vlm()
    offload_llm()

    try:
        import torch
        if torch.backends.mps.is_available():
            mps_gib = torch.mps.driver_allocated_memory() / 1024**3
            print(f"[TTS load] MPS driver memory before TTS load: {mps_gib:.2f} GiB")
    except Exception:
        pass

    detail = "Loading weights…" if _hf_cached(_TTS_REPO) else "Downloading from HuggingFace…"
    _set("tts", "sync", "loading", detail)
    try:
        from postprocessing.translate_tts import _use_nanovllm
        if _use_nanovllm():
            from postprocessing import get_voxcpm2_model_nano
            tts_instance = get_voxcpm2_model_nano()
            _set("tts", "check_circle", "ready", "Ready (nanovllm)")
        else:
            from postprocessing import get_voxcpm2_model
            tts_instance, _sr = get_voxcpm2_model()
            _set("tts", "check_circle", "ready", "Ready")
        with _LOCK:
            _INSTANCES["tts"] = tts_instance
        return tts_instance
    except Exception as exc:
        _set("tts", "error", "error", str(exc)[:120])
        return None


def start() -> None:
    global _started
    if _started:
        return
    _started = True
    threading.Thread(target=_load_models, daemon=True, name="eyas-model-preloader").start()
