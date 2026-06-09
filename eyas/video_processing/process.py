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

import json
import re
from dataclasses import dataclass, field
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
        self.backend = "minicpmv"

    # -- model loading -------------------------------------------------------
    def _ensure_loaded(self) -> None:
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
