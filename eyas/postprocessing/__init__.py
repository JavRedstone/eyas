import os

TINYAYA_LANGUAGES_BY_REGION = {
    "South Asia": [
        "Telugu", "Marathi", "Bengali", "Tamil", "Hindi",
        "Punjabi", "Gujarati", "Urdu", "Nepali"
    ],
    "Asia Pacific": [
        "Traditional Chinese", "Cantonese", "Vietnamese", "Tagalog", "Javanese",
        "Khmer", "Thai", "Burmese", "Malay", "Korean",
        "Lao", "Indonesian", "Simplified Chinese", "Japanese"
    ],
    "Europe": [
        "Catalan", "Galician", "Dutch", "Danish", "Finnish",
        "Czech", "Portuguese", "French", "Lithuanian", "Slovak",
        "Basque", "English", "Swedish", "Polish", "Spanish",
        "Slovenian", "Ukrainian", "Greek", "Bokmål", "Romanian",
        "Serbian", "German", "Italian", "Russian", "Irish",
        "Hungarian", "Bulgarian", "Croatian", "Estonian", "Latvian", "Welsh"
    ],
    "Africa": [
        "Zulu", "Amharic", "Hausa", "Igbo", "Swahili",
        "Xhosa", "Wolof", "Shona", "Yoruba", "Nigerian Pidgin", "Malagasy"
    ],
    "West Asia": [
        "Arabic", "Maltese", "Turkish", "Hebrew", "Persian"
    ]
}

TINYAYA_SUPPORTED_LANGUAGES = {
    lang for langs in TINYAYA_LANGUAGES_BY_REGION.values() for lang in langs
}

TINYAYA_GGUF_REPO = "CohereLabs/tiny-aya-global-GGUF"
TINYAYA_GGUF_FILE = os.getenv("EYAS_TINYAYA_GGUF_FILE", "tiny-aya-global-q4_k_m.gguf")

_tinyaya_models: dict[bool, object] = {}


def get_tinyaya_model(use_gpu: bool = True):
    """Lazy-load tiny-aya-global via llama-cpp-python."""
    if use_gpu in _tinyaya_models:
        return _tinyaya_models[use_gpu]
    try:
        from llama_cpp import Llama  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "llama-cpp-python is not installed. Run: pip install llama-cpp-python"
        ) from exc
    n_gpu_layers = -1 if use_gpu else 0
    _tinyaya_models[use_gpu] = Llama.from_pretrained(
        repo_id=TINYAYA_GGUF_REPO,
        filename=TINYAYA_GGUF_FILE,
        n_ctx=int(os.getenv("EYAS_TINYAYA_N_CTX", "4096")),
        n_gpu_layers=n_gpu_layers,
        verbose=False,
    )
    return _tinyaya_models[use_gpu]


_voxcpm2_model = None
_voxcpm2_sample_rate = None


def get_voxcpm2_model():
    """Lazy-load VoxCPM2 via the standard PyTorch voxcpm backend (MPS / CPU / ZeroGPU)."""
    global _voxcpm2_model, _voxcpm2_sample_rate
    if _voxcpm2_model is not None:
        return _voxcpm2_model, _voxcpm2_sample_rate
    from voxcpm import VoxCPM

    import torch
    _voxcpm2_model = VoxCPM.from_pretrained(
        "openbmb/VoxCPM2", device="auto", load_denoiser=False,
        optimize=torch.cuda.is_available(),
    )
    _voxcpm2_sample_rate = _voxcpm2_model.tts_model.sample_rate
    return _voxcpm2_model, _voxcpm2_sample_rate


# VoxCPM2 AudioVAE output sample rate (from model config; same for both backends).
VOXCPM2_NANO_SAMPLE_RATE: int = 16000

_voxcpm2_nano_server = None


def get_voxcpm2_model_nano():
    """Lazy-load VoxCPM2 via nanovllm_voxcpm (bare CUDA / dedicated GPU only).

    Returns a SyncVoxCPMServerPool.  Do NOT use on ZeroGPU — the persistent
    worker processes lose GPU access when the @spaces.GPU window closes.
    """
    global _voxcpm2_nano_server
    if _voxcpm2_nano_server is not None:
        return _voxcpm2_nano_server
    try:
        from nanovllm_voxcpm import VoxCPM as NanoVoxCPM  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "nano-vllm-voxcpm is not installed. Run: pip install nano-vllm-voxcpm"
        ) from exc
    _voxcpm2_nano_server = NanoVoxCPM.from_pretrained(
        model="openbmb/VoxCPM2",
        devices=[0],
        max_num_batched_tokens=4096,
        max_num_seqs=4,
        gpu_memory_utilization=0.8,
    )
    return _voxcpm2_nano_server

VOXCPM2_SUPPORTED_LANGUAGES = [
    "Arabic", "Burmese", "Simplified Chinese", "Traditional Chinese", "Danish", "Dutch", "English", "Finnish", "French",
    "German", "Greek", "Hebrew", "Hindi", "Indonesian", "Italian", "Japanese", "Khmer",
    "Korean", "Lao", "Malay", "Norwegian", "Polish", "Portuguese", "Russian", "Spanish",
    "Swahili", "Swedish", "Tagalog", "Thai", "Turkish", "Vietnamese"
]
