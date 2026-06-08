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

_tinyaya_model = None


def get_tinyaya_model():
    """Lazy-load tiny-aya-global via llama-cpp-python."""
    global _tinyaya_model
    if _tinyaya_model is not None:
        return _tinyaya_model
    try:
        from llama_cpp import Llama  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "llama-cpp-python is not installed. Run: pip install llama-cpp-python"
        ) from exc
    _tinyaya_model = Llama.from_pretrained(
        repo_id=TINYAYA_GGUF_REPO,
        filename=TINYAYA_GGUF_FILE,
        n_ctx=int(os.getenv("EYAS_TINYAYA_N_CTX", "4096")),
        n_gpu_layers=int(os.getenv("EYAS_N_GPU_LAYERS", "-1")),
        verbose=False,
    )
    return _tinyaya_model


from voxcpm import VoxCPM
VOXCPM2_MODEL = VoxCPM.from_pretrained("openbmb/VoxCPM2", device="auto", load_denoiser=False)
TTS_SAMPLE_RATE = VOXCPM2_MODEL.tts_model.sample_rate

VOXCPM2_SUPPORTED_LANGUAGES = [
    "Arabic", "Burmese", "Simplified Chinese", "Traditional Chinese", "Danish", "Dutch", "English", "Finnish", "French",
    "German", "Greek", "Hebrew", "Hindi", "Indonesian", "Italian", "Japanese", "Khmer",
    "Korean", "Lao", "Malay", "Norwegian", "Polish", "Portuguese", "Russian", "Spanish",
    "Swahili", "Swedish", "Tagalog", "Thai", "Turkish", "Vietnamese"
]
