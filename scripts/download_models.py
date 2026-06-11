"""Pre-download models at Docker build time."""
import os
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "eyas"))

models_dir = os.path.join(os.path.dirname(__file__), "..", "eyas", "models")
os.makedirs(models_dir, exist_ok=True)

# YOLO 11n — download from Ultralytics releases
yolo_path = os.path.join(models_dir, "yolo11n.pt")
if not os.path.exists(yolo_path):
    print("Downloading YOLO 11n...")
    urllib.request.urlretrieve(
        "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt",
        yolo_path,
    )
    print("✓ YOLO downloaded")
else:
    print("✓ YOLO already present")

# Nemotron GGUF — LLM reasoner (downloads to HF cache, loaded from there)
print("Downloading Nemotron GGUF...")
from llama_cpp import Llama  # noqa: E402
Llama.from_pretrained(
    repo_id="nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF",
    filename="NVIDIA-Nemotron3-Nano-4B-Q4_K_M.gguf",
    verbose=False,
)
print("✓ Nemotron downloaded")

# TinyAya GGUF — translation model
print("Downloading TinyAya GGUF...")
from huggingface_hub import hf_hub_download  # noqa: E402
hf_hub_download(
    repo_id="CohereLabs/tiny-aya-global-GGUF",
    filename="tiny-aya-global-q4_k_m.gguf",
)
print("✓ TinyAya downloaded")

# VoxCPM2 TTS + MiniCPM-V VLM are large transformers models;
# they download automatically on first startup via huggingface_hub.
print("Done. VLM/TTS will download on first startup.")
