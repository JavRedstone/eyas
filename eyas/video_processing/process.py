"""Object identity / VLM layer — MiniCPM-V 4.6 (OpenBMB, 1.3B).

Scope (Eyas visual pipeline):
    This is the *semantic layer*. YOLO (object_detection/detector.py) provides
    persistent person tracks. MiniCPM-V continuously observes the previous and
    current crop for each track, describing the person, their latest action,
    and visible items. Event structuring retains that context for the visit.

Model: openbmb/MiniCPM-V-4.6  (1.3B params — pocket-sized, edge/on-device)
    - SigLIP2-400M vision + Qwen3.5-0.8B LLM.
    - Native transformers API (transformers>=5.7.0):
        processor.apply_chat_template(...) -> model.generate(...)
      (NOTE: this differs from MiniCPM-o 4.5's model.chat() API.)
    - ~3GB bf16 — small enough to run on a laptop GPU / Apple Silicon (MPS),
      or quantized (GGUF/AWQ/BNB/GPTQ) for CPU.

The visual pipeline always runs the real local MiniCPM-V model.
"""

from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

MODEL_ID = "openbmb/MiniCPM-V-4.6"

# Default prompt tuned for the retail "what did this person take" task.
RETAIL_PROMPT = (
    "You are watching CCTV of a convenience store. A single person is the focus "
    "of this clip. List ONLY the retail products this person picks up, takes, or "
    "holds, with a count for each. Use the format 'qty x item' per line, e.g. "
    "'2 x bag of chips'. If you are unsure of a brand, describe the product "
    "generically (e.g. 'bottle of soda'). If they take nothing, reply 'nothing'."
)

PERSON_STATUS_PROMPT = (
    "You are observing one YOLO-tracked person in convenience-store CCTV. "
    "The ordered images were selected because motion near the person may show an "
    "interaction; treat them as before, during, and after evidence. "
    "Describe only what is visibly present in the supplied images. Give a short "
    "non-biometric appearance description useful during this visit, then state "
    "what the person is currently doing. Set held_objects only for objects with "
    "clear visible contact with the person's hand. An object near a hand, on a "
    "shelf, or merely inside the person's bounding box is not held. When hand "
    "contact is unclear, return an empty held_objects list. "
    "The supplied images are chronological, oldest first and newest last. "
    "Determine separately whether the ordered images "
    "clearly show the person's hand contacting a retail item and the item moving "
    "from its previous location into the person's hand. An item merely inside "
    "the bounding box, on a nearby shelf, or already visible is NOT a pickup. "
    "If the sequence shows the hand moving toward an item and then holding it, "
    "describe the activity explicitly as picking up the item. Do not use only "
    "the vague phrase 'interacting with retail items' for a visible pickup. "
    "Set pickup_confirmed=true only when this hand-contact plus movement is "
    "clearly visible across the images. Do not infer identity, intent, theft, "
    "ownership, colors that are not clearly visible, or events outside these "
    "images. Return ONLY JSON with the keys description, activity, held_objects, "
    "pickup_confirmed, and picked_up_items. held_objects and picked_up_items "
    "must be arrays of objects containing name and count. Default both arrays "
    "to empty and pickup_confirmed to false unless the images clearly prove "
    "otherwise."
)

LLAMA_CPP_FRAME_PROMPT = (
    "The labeled images above are chronological evidence of the same tracked "
    "person. Compare FRAME 1 through the newest frame carefully. Pay particular "
    "attention to the person's clothing, hands, and whether an object changes "
    "from being on a shelf to being visibly held. Do not reuse a generic answer "
    "from another observation. Do not mistake the color of a nearby or held "
    "product for the color of the person's clothing. Set pickup_confirmed=true "
    "only if the frames visibly prove a shelf-to-hand transition involving a "
    "specific product. Words such as appears, possibly, suggesting, or may mean "
    "pickup_confirmed must be false. "
)


@dataclass
class ClipAnnotation:
    """Semantic result for one analysed clip/event."""

    caption: str                         # raw natural-language model output
    items: List[Dict] = field(default_factory=list)  # [{"name","qty"}, ...]
    track_id: Optional[int] = None
    backend: str = "minicpmv"

    def summary(self) -> str:
        """Human sentence, e.g. 'the person took 2 bags of chips and 1 coke'."""
        if not self.items:
            return self.caption or "no items detected"
        parts = [f"{it['qty']} {it['name']}" for it in self.items]
        if len(parts) == 1:
            listed = parts[0]
        else:
            listed = ", ".join(parts[:-1]) + " and " + parts[-1]
        return f"the person took {listed}"


@dataclass
class PersonObservation:
    """One real-time semantic observation for a persistent YOLO track."""

    description: str = ""
    activity: str = ""
    held_objects: List[Dict] = field(default_factory=list)
    pickup_confirmed: bool = False
    picked_up_items: List[Dict] = field(default_factory=list)
    raw: str = ""
    track_id: Optional[int] = None
    backend: str = "minicpmv"


# ---------------------------------------------------------------------------
# Item parsing: turn free-text VLM output into [{"name","qty"}] structure.
# ---------------------------------------------------------------------------
_LINE_QTY = re.compile(
    r"^\s*(?:[-*\d.]+\s*)?(\d+)\s*(?:x|\*|×)?\s+(.*?)\s*$", re.IGNORECASE
)
_WORD_NUM = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}
_NON_PRODUCT_ITEMS = {
    "glasses", "eyeglasses", "sunglasses", "hat", "cap", "shirt", "t-shirt",
    "pants", "jeans", "shoes", "jacket", "coat", "hair",
}
_EXPLICIT_HELD_OBJECT = re.compile(
    r"\b(?:holding|carrying)\s+"
    r"(?:(\d+|a|an|one|two|three|four|five)\s+)?"
    r"(.+?)(?=,\s*|\s+in\s+(?:his|her|their|the)\s+(?:left|right)?\s*hand\b|"
    r"\s+while\b|\s+and\s+(?:walking|moving|looking|standing)\b|$)",
    re.IGNORECASE,
)
_HELD_NEGATION = re.compile(r"\b(?:not|isn't|is\s+not|aren't|are\s+not|without)\b", re.IGNORECASE)


def parse_items(text: str) -> List[Dict]:
    """Parse 'qty x item' lines (and a few natural variants) into structured items."""
    items: List[Dict] = []
    if not text:
        return items
    for raw in re.split(r"[\n;]", text):
        line = raw.strip().strip(".")
        normalized = line.lower()
        if (
            not line
            or normalized in {"nothing", "none", "no items"}
            or "nothing" in normalized
            or normalized.startswith(("no retail product", "no product", "no item"))
        ):
            continue
        m = _LINE_QTY.match(line)
        if m:
            qty = int(m.group(1))
            name = m.group(2).strip()
        else:
            toks = line.split()
            if toks and toks[0].lower() in _WORD_NUM:
                qty = _WORD_NUM[toks[0].lower()]
                name = " ".join(toks[1:]).strip()
            else:
                qty = 1
                name = line
        name = re.sub(r"\s+", " ", name).strip(" .-").lower()
        if name:
            items.append({"name": name, "qty": qty})
    return items


def parse_person_observation(text: str) -> PersonObservation:
    """Parse the VLM's JSON status response, tolerating fenced JSON."""
    if not text:
        return PersonObservation(raw=text)
    normalized_text = re.sub(r"^\s*\{=\s*", "{", text.strip())
    decoder = json.JSONDecoder()
    objects = []
    position = 0
    while position < len(normalized_text):
        start = normalized_text.find("{", position)
        if start < 0:
            break
        try:
            value, end = decoder.raw_decode(normalized_text[start:])
            if isinstance(value, dict):
                objects.append(value)
            position = start + end
        except json.JSONDecodeError:
            position = start + 1

    description = ""
    activity = ""
    pickup_confirmed = False
    raw_items = []
    raw_held_objects = []
    for data in objects:
        description = str(data.get("description", "")).strip() or description
        activity = str(data.get("activity", data.get("action", ""))).strip() or activity
        pickup_confirmed = pickup_confirmed or data.get("pickup_confirmed") is True
        if isinstance(data.get("picked_up_items"), list):
            raw_items = data["picked_up_items"]
        if isinstance(data.get("held_objects"), list):
            raw_held_objects = data["held_objects"]

    # Tolerate partially malformed JSON fields while never defaulting a pickup
    # to true. Missing/invalid confirmation remains false.
    if not description:
        match = re.search(r'"description"\s*:\s*"([^"]+)"', normalized_text)
        description = match.group(1).strip() if match else ""
    if not activity:
        match = re.search(r'"(?:activity|action)"\s*:\s*"([^"]+)"', normalized_text)
        activity = match.group(1).strip() if match else ""
    if re.search(r'"pickup_confirmed"\s*:\s*true\b', normalized_text, re.IGNORECASE):
        pickup_confirmed = True

    picked_up_items = []
    for item in raw_items:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        try:
            count = max(1, int(item.get("count", 1)))
        except (TypeError, ValueError):
            count = 1
        name = str(item["name"]).strip().lower()
        if name not in _NON_PRODUCT_ITEMS:
            picked_up_items.append({"name": name, "count": count})
    if not pickup_confirmed:
        picked_up_items = []
    held_objects = []
    for item in raw_held_objects:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        try:
            count = max(1, int(item.get("count", 1)))
        except (TypeError, ValueError):
            count = 1
        name = str(item["name"]).strip().lower()
        if name not in _NON_PRODUCT_ITEMS:
            held_objects.append({"name": name, "count": count})
    if not held_objects:
        explicit_held = _EXPLICIT_HELD_OBJECT.search(f"{description}, {activity}")
        if explicit_held:
            prefix = f"{description}, {activity}"[
                max(0, explicit_held.start() - 12):explicit_held.start()
            ]
            if _HELD_NEGATION.search(prefix):
                explicit_held = None
        if explicit_held:
            token = (explicit_held.group(1) or "1").lower()
            count = int(token) if token.isdigit() else _WORD_NUM.get(token, 1)
            name = explicit_held.group(2).strip(" .").lower()
            if name not in _NON_PRODUCT_ITEMS:
                held_objects.append({"name": name, "count": count})
    if description and not activity:
        current = re.search(r"[;,]?\s*currently\s+(.+)$", description, re.IGNORECASE)
        trailing = re.search(
            r"\s+and\s+((?:raising|holding|picking|taking|reaching|carrying)\b.+)$",
            description,
            re.IGNORECASE,
        )
        action_match = current or trailing
        if action_match:
            activity = action_match.group(1).strip()
            description = description[:action_match.start()].rstrip(" ,;")
    return PersonObservation(
        description=description,
        activity=activity,
        held_objects=held_objects,
        pickup_confirmed=pickup_confirmed,
        picked_up_items=picked_up_items,
        raw=text,
    )


# ---------------------------------------------------------------------------
# Backend: real MiniCPM-V 4.6
# ---------------------------------------------------------------------------
class MiniCPMVLM:
    """Vision MiniCPM-V 4.6 wrapper for clip/crop captioning.

    Lazy-loads the real local model on first use.

    Args:
        model_id:   HF model id (or a quantized variant).
        device_map: passed to from_pretrained ("auto"). On Mac, set device="mps".
        dtype:      "auto" lets transformers pick; or "bfloat16"/"float16".
        attn:       "sdpa" (safe everywhere) or "flash_attention_2" (CUDA).
    """

    def __init__(
        self,
        model_id: str = MODEL_ID,
        device: Optional[str] = None,   # None -> use device_map="auto"
        dtype: str = "auto",
        attn: str = "sdpa",
        downsample_mode: str = "16x",
        max_image_size: int = 448,
        max_new_tokens: int = 96,
    ) -> None:
        self.model_id = model_id
        self.device = device
        self.dtype = dtype
        self.attn = attn
        self.downsample_mode = downsample_mode
        self.max_image_size = max(0, max_image_size)
        self.max_new_tokens = max(32, max_new_tokens)
        self.model = None
        self.processor = None
        self._loaded = False
        self._offloaded = False  # True when model is on CPU after offload()
        self.backend = "minicpmv"

    # -- model loading -------------------------------------------------------
    def offload(self) -> None:
        """Free GPU VRAM. On explicit device: moves weights to CPU (fast restore).
        With device_map=auto: deletes model object; reloads from HF local cache on next use."""
        import gc
        if self.model is None:
            return
        try:
            import torch
            # Flush all pending GPU work before touching the model object.
            # On MPS (Apple Silicon) this prevents Metal command-encoder conflicts.
            if self.device == "mps" and getattr(torch, "backends", None) and torch.backends.mps.is_available():
                torch.mps.synchronize()
            elif torch.cuda.is_available():
                torch.cuda.synchronize()
            if self.device:
                self.model.to("cpu")
                self._offloaded = True
            else:
                del self.model
                self.model = None
                self._loaded = False
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
        gc.collect()

    def _ensure_loaded(self) -> None:
        if self._offloaded:
            # Restore from CPU back to the target device.
            try:
                self.model.to(self.device)
                self._offloaded = False
                return
            except Exception:
                # Restore failed — fall through to full reload.
                self._offloaded = False
                self._loaded = False
                self.model = None
        if self._loaded:
            return
        import torch
        try:
            from transformers import AutoModelForImageTextToText, AutoProcessor
        except ImportError as exc:
            raise RuntimeError(
                "MiniCPM-V 4.6 requires a Transformers release that provides "
                "AutoModelForImageTextToText. Install this project's visual "
                "dependencies with: pip install -r requirements.txt"
            ) from exc

        self.processor = AutoProcessor.from_pretrained(self.model_id)
        torch_dtype = self.dtype if self.dtype == "auto" else getattr(torch, self.dtype)
        kwargs = dict(dtype=torch_dtype, attn_implementation=self.attn)
        if self.device:                      # explicit device (e.g. 'mps')
            self.model = AutoModelForImageTextToText.from_pretrained(
                self.model_id, **kwargs
            ).to(self.device)
        else:                                # let accelerate place it
            self.model = AutoModelForImageTextToText.from_pretrained(
                self.model_id, device_map="auto", **kwargs
            )
        self.model.eval()
        self._loaded = True

    # -- inference -----------------------------------------------------------
    def _to_pil(self, frame: np.ndarray):
        from PIL import Image

        if frame.ndim == 3 and frame.shape[2] == 3:
            frame = frame[:, :, ::-1]        # BGR (cv2) -> RGB
        image = Image.fromarray(np.ascontiguousarray(frame))
        if self.max_image_size and max(image.size) > self.max_image_size:
            image.thumbnail((self.max_image_size, self.max_image_size))
        return image

    def caption_frames(
        self,
        frames: List[np.ndarray],
        prompt: str = RETAIL_PROMPT,
        track_id: Optional[int] = None,
        max_new_tokens: int = 192,
    ) -> ClipAnnotation:
        """Caption a list of BGR frames (a sampled clip) and parse items out.

        Frames are passed as multi-image content with video-style settings
        (use_image_id=False, max_slice_nums=1) per the model card.
        """
        if not frames:
            return ClipAnnotation(
                caption="no frames supplied",
                track_id=track_id,
                backend=self.backend,
            )
        self._ensure_loaded()
        images = [self._to_pil(f) for f in frames]
        content = [{"type": "image", "image": img} for img in images]
        content.append({"type": "text", "text": prompt})
        messages = [{"role": "user", "content": content}]

        inputs = self.processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
            processor_kwargs={
                "downsample_mode": self.downsample_mode,
                "max_slice_nums": 1,    # video/multi-frame recommendation
                "use_image_id": False,  # do not tag each frame separately
            },
        ).to(self.model.device)

        gen = self.model.generate(
            **inputs,
            downsample_mode=self.downsample_mode,
            max_new_tokens=max_new_tokens,
            do_sample=False,
        )
        trimmed = [out[len(inp):] for inp, out in zip(inputs.input_ids, gen)]
        text = self.processor.batch_decode(
            trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]
        text = text.strip()
        return ClipAnnotation(
            caption=text,
            items=parse_items(text),
            track_id=track_id,
            backend="minicpmv",
        )

    def observe_person(
        self,
        frames: List[np.ndarray],
        track_id: Optional[int] = None,
        max_new_tokens: Optional[int] = None,
    ) -> PersonObservation:
        """Describe a tracked person and their latest action from live snapshots."""
        if not frames:
            return PersonObservation(
                activity="no frames supplied",
                track_id=track_id,
                backend=self.backend,
            )
        self._ensure_loaded()
        images = [self._to_pil(frame) for frame in frames[-5:]]
        content = [{"type": "image", "image": image} for image in images]
        content.append({"type": "text", "text": PERSON_STATUS_PROMPT})
        messages = [{"role": "user", "content": content}]
        inputs = self.processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
            processor_kwargs={
                "downsample_mode": self.downsample_mode,
                "max_slice_nums": 1,
                "use_image_id": False,
            },
        ).to(self.model.device)
        generated = self.model.generate(
            **inputs,
            downsample_mode=self.downsample_mode,
            max_new_tokens=max_new_tokens or self.max_new_tokens,
            do_sample=False,
            use_cache=True,
        )
        trimmed = [out[len(inp):] for inp, out in zip(inputs.input_ids, generated)]
        text = self.processor.batch_decode(
            trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0].strip()
        observation = parse_person_observation(text)
        observation.track_id = track_id
        observation.backend = "minicpmv"
        return observation


class LlamaCppMiniCPMVLM:
    """MiniCPM-V 4.6 GGUF backend using llama-cpp-python.

    The official MiniCPM-V 4.6 GGUF repository supports multimodal
    ``create_chat_completion`` calls in recent llama-cpp-python builds. Images
    are passed as in-memory data URIs so the pipeline never writes crop files.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        mmproj_path: Optional[str] = None,
        repo_id: str = "openbmb/MiniCPM-V-4.6-gguf",
        filename: str = "MiniCPM-V-4_6-F16.gguf",
        mmproj_filename: str = "mmproj-model-f16.gguf",
        n_ctx: int = 8192,
        n_threads: Optional[int] = None,
        n_gpu_layers: int = -1,
        max_image_size: int = 448,
        max_new_tokens: int = 96,
        verbose: bool = False,
    ) -> None:
        self.model_path = model_path
        self.mmproj_path = mmproj_path
        self.repo_id = repo_id
        self.filename = filename
        self.mmproj_filename = mmproj_filename
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.n_gpu_layers = n_gpu_layers
        self.max_image_size = max(0, max_image_size)
        self.max_new_tokens = max(32, max_new_tokens)
        self.verbose = verbose
        self.model = None
        self._loaded = False
        self.backend = "llama-cpp-python"

    def _resolve_local_gguf(self, requested: str, pattern: str, label: str) -> Path:
        """Resolve a requested GGUF, tolerating official-repo filename variants."""
        path = Path(requested).expanduser().resolve()
        if path.exists():
            return path
        matches = sorted(path.parent.glob(pattern)) if path.parent.exists() else []
        if len(matches) == 1:
            print(f"[llama-cpp-python] using {label}: {matches[0]}")
            return matches[0].resolve()
        available = ", ".join(match.name for match in matches) or "none"
        raise FileNotFoundError(
            f"{label} not found at {path}. Matching files beside it: {available}"
        )

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        try:
            from llama_cpp import Llama
            from llama_cpp.llama_chat_format import MTMDChatHandler
        except ImportError as exc:
            raise RuntimeError(
                "llama-cpp-python is not installed. On Apple Silicon, install "
                "a Metal build with: CMAKE_ARGS='-DGGML_METAL=on "
                "-DGGML_ACCELERATE=on' pip install --upgrade --force-reinstall "
                "llama-cpp-python"
            ) from exc

        if self.mmproj_path:
            mmproj = self._resolve_local_gguf(
                self.mmproj_path, "*mmproj*.gguf", "vision projector"
            )
        else:
            try:
                from huggingface_hub import hf_hub_download
            except ImportError as exc:
                raise RuntimeError(
                    "Install huggingface-hub or pass --llama-mmproj-path."
                ) from exc
            mmproj = Path(
                hf_hub_download(repo_id=self.repo_id, filename=self.mmproj_filename)
            )
        try:
            chat_handler = MTMDChatHandler(
                clip_model_path=str(mmproj),
                verbose=self.verbose,
                use_gpu=self.n_gpu_layers != 0,
            )
        except Exception as exc:
            raise RuntimeError(
                "The installed llama-cpp-python build cannot initialize the "
                "MiniCPM-V 4.6 vision projector. Install a recent "
                "libmtmd-enabled build."
            ) from exc

        kwargs = {
            "n_ctx": self.n_ctx,
            "n_gpu_layers": self.n_gpu_layers,
            "verbose": self.verbose,
            "chat_handler": chat_handler,
        }
        if self.n_threads is not None:
            kwargs["n_threads"] = self.n_threads
        try:
            if self.model_path:
                path = self._resolve_local_gguf(
                    self.model_path, "*MiniCPM*F16.gguf", "language model"
                )
                self.model = Llama(model_path=str(path), **kwargs)
            else:
                self.model = Llama.from_pretrained(
                    repo_id=self.repo_id,
                    filename=self.filename,
                    **kwargs,
                )
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                "The installed llama-cpp-python build cannot load MiniCPM-V "
                "4.6 multimodal GGUF files. Install a recent libmtmd-enabled "
                "build, or keep using the Transformers backend."
            ) from exc
        self._loaded = True

    def _to_data_uri(self, frame: np.ndarray) -> str:
        import cv2

        image = frame
        if self.max_image_size and max(image.shape[:2]) > self.max_image_size:
            scale = self.max_image_size / max(image.shape[:2])
            image = cv2.resize(
                image,
                (
                    max(1, round(image.shape[1] * scale)),
                    max(1, round(image.shape[0] * scale)),
                ),
                interpolation=cv2.INTER_AREA,
            )
        # Lossless PNG preserves small products and hand/object boundaries.
        ok, encoded = cv2.imencode(".png", image)
        if not ok:
            raise RuntimeError("Could not encode a VLM crop as PNG")
        payload = base64.b64encode(encoded.tobytes()).decode("ascii")
        return f"data:image/png;base64,{payload}"

    def _complete(self, frames: List[np.ndarray], prompt: str, max_tokens: int) -> str:
        self._ensure_loaded()
        content = []
        for index, frame in enumerate(frames, start=1):
            age = "oldest" if index == 1 else "newest" if index == len(frames) else ""
            label = f"FRAME {index}" + (f" ({age})" if age else "")
            content.append({"type": "text", "text": label})
            content.append(
                {"type": "image_url", "image_url": {"url": self._to_data_uri(frame)}}
            )
        content.append({"type": "text", "text": LLAMA_CPP_FRAME_PROMPT + prompt})
        try:
            response = self.model.create_chat_completion(
                messages=[{"role": "user", "content": content}],
                temperature=0.0,
                top_k=1,
                repeat_penalty=1.05,
                response_format={"type": "json_object"},
                max_tokens=max_tokens,
            )
        except Exception as exc:
            raise RuntimeError(
                "The installed llama-cpp-python build could not process "
                "MiniCPM-V 4.6 image messages. On Metal, llama_decode failures "
                "can indicate an incompatible llama-cpp-python build. Install "
                "a recent MiniCPM-V 4.6/libmtmd build, or use Transformers."
            ) from exc
        choice = response.get("choices", [{}])[0]
        text = choice.get("message", {}).get("content") or choice.get("text", "")
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError(
                "llama-cpp-python returned no multimodal text. The installed "
                "build may not support MiniCPM-V 4.6 image input."
            )
        return text.strip()

    def caption_frames(
        self,
        frames: List[np.ndarray],
        prompt: str = RETAIL_PROMPT,
        track_id: Optional[int] = None,
        max_new_tokens: int = 192,
    ) -> ClipAnnotation:
        if not frames:
            return ClipAnnotation(
                caption="no frames supplied",
                track_id=track_id,
                backend=self.backend,
            )
        text = self._complete(frames, prompt, max_new_tokens)
        return ClipAnnotation(
            caption=text,
            items=parse_items(text),
            track_id=track_id,
            backend=self.backend,
        )

    def observe_person(
        self,
        frames: List[np.ndarray],
        track_id: Optional[int] = None,
        max_new_tokens: Optional[int] = None,
    ) -> PersonObservation:
        if not frames:
            return PersonObservation(
                activity="no frames supplied",
                track_id=track_id,
                backend=self.backend,
            )
        text = self._complete(
            frames[-5:],
            PERSON_STATUS_PROMPT,
            max_new_tokens or self.max_new_tokens,
        )
        observation = parse_person_observation(text)
        observation.track_id = track_id
        observation.backend = self.backend
        return observation


# ---------------------------------------------------------------------------
# Module-level convenience matching the original scaffold signature.
# ---------------------------------------------------------------------------
_default_vlm: Optional[MiniCPMVLM] = None


def get_vlm(**kwargs) -> MiniCPMVLM:
    global _default_vlm
    if _default_vlm is None:
        _default_vlm = MiniCPMVLM(**kwargs)
    return _default_vlm


def process_clip(path: str) -> List[Dict]:
    """Legacy entry point: read a clip file, caption it, return annotation dicts.

    Prefer MiniCPMVLM.caption_frames() for the in-memory (ringbuffer) path.
    """
    import cv2

    from .buffer import sample_frames

    cap = cv2.VideoCapture(path)
    frames = []
    while cap.isOpened():
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    cap.release()
    frames = sample_frames(frames, k=8)
    ann = get_vlm().caption_frames(frames)
    return [{
        "caption": ann.caption,
        "items": ann.items,
        "summary": ann.summary(),
        "backend": ann.backend,
    }]
