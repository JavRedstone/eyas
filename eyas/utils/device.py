"""Device selection utility: picks the best available PyTorch backend."""

from __future__ import annotations


def get_device() -> str:
    """Return 'cuda', 'mps', or 'cpu' — whichever is available, in that order."""
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return "mps"
    except ImportError:
        pass
    return "cpu"
