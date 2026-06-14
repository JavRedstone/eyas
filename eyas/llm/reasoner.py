"""LLM reasoning wrapper using llama-cpp-python for local inference."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from .prompts import (
    ALERT_GRAMMAR,
    ALERT_PROMPT,
    QA_GRAMMAR,
    QA_PROMPT,
    SUMMARIZE_GRAMMAR,
    SUMMARIZE_PROMPT,
    SYSTEM_PROMPT,
)

# ---------------------------------------------------------------------------
# Fallback dicts returned when JSON parsing fails
# ---------------------------------------------------------------------------
_SUMMARIZE_FALLBACK: Dict = {
    "summary": "LLM summary unavailable.",
    "flags": [],
    "suspicious_clips": [],
    "risk_level": "none",
}
_QA_FALLBACK: Dict = {"answer": "", "relevant_event_indices": [], "clips": []}
_ALERT_FALLBACK: Dict = {"alert": "", "severity": "low", "clip": ""}

_NEMOTRON_REPO_ID = "nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF"
_NEMOTRON_GGUF_FILENAME = "NVIDIA-Nemotron3-Nano-4B-Q4_K_M.gguf"
_DEFAULT_LOCAL_MODEL = "nemotron-nano-4b.gguf"


def _short_item_name(item: dict) -> str:
    """Truncate item name to first phrase — prevents VLM scene descriptions bleeding in."""
    name = item.get("name", "") if isinstance(item, dict) else str(item)
    for sep in [". ", "; ", ", and "]:
        if sep in name:
            name = name[: name.index(sep)]
    return name[:45].strip()


class Reasoner:
    """Local LLM reasoning engine backed by llama-cpp-python."""

    def __init__(
        self,
        model_path: str,
        n_ctx: int = 4096,
        n_gpu_layers: int = -1,
    ) -> None:
        self._model_path = model_path
        self._n_ctx = n_ctx
        self._n_gpu_layers = n_gpu_layers
        self._model = None  # lazy-loaded on first call

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_model(self) -> None:
        if self._model is not None:
            return
        local_path = Path(self._model_path).expanduser()
        if local_path.is_file():
            try:
                from llama_cpp import Llama  # type: ignore
            except ImportError as exc:
                raise RuntimeError(
                    "llama-cpp-python is not installed. Run: pip install llama-cpp-python"
                ) from exc
            self._model = Llama(
                model_path=str(local_path),
                n_ctx=self._n_ctx,
                n_gpu_layers=self._n_gpu_layers,
                verbose=False,
            )
            return

        if local_path.name not in {_DEFAULT_LOCAL_MODEL, _NEMOTRON_GGUF_FILENAME}:
            raise RuntimeError(
                f"Model file not found: {self._model_path!r}. "
                "Set EYAS_MODEL_PATH to an existing GGUF file or use the default "
                "Nemotron path to download from Hugging Face."
            )

        try:
            from llama_cpp import Llama  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "llama-cpp-python is not installed. Run: pip install llama-cpp-python"
            ) from exc

        self._model = Llama.from_pretrained(
            repo_id=_NEMOTRON_REPO_ID,
            filename=_NEMOTRON_GGUF_FILENAME,
            n_ctx=self._n_ctx,
            n_gpu_layers=self._n_gpu_layers,
            verbose=False,
        )

    def offload(self) -> None:
        """Free Metal/GPU memory held by the llama.cpp Llama object.
        The model reloads automatically from disk on the next summarize call."""
        if self._model is not None:
            print("[LLM offload] Freeing llama.cpp Metal memory…")
            try:
                self._model.close()
            except Exception:
                pass
            try:
                del self._model
            except Exception:
                pass
            self._model = None
            import gc

            gc.collect()
            print("[LLM offload] Done.")

    @staticmethod
    def _is_observation_schema(ev: Dict) -> bool:
        """True for ObservationEvent dicts (structurer output); False for legacy dicts."""
        return "timestamp" in ev and "activity" in ev and "track_id" in ev

    @staticmethod
    def _format_observation(i: int, ev: Dict, cam_label: str = "") -> str:
        conf = ev.get("confidence", "?")
        conf_s = f"{conf:.2f}" if isinstance(conf, float) else str(conf)
        held = ev.get("held_objects") or []
        held_s = (
            ", ".join(f"{_short_item_name(h)} x{h.get('count', 1)}" for h in held)
            if held
            else "-"
        )
        pickup = ev.get("pickup_confirmed", False)
        picked = ev.get("picked_up_items") or []
        if pickup:
            item_list = ", ".join(f"{_short_item_name(p)} x{p.get('count', 1)}" for p in picked)
            pickup_s = f"YES -> {item_list}" if item_list else "YES (item unidentified)"
        else:
            pickup_s = "no"
        summary = (ev.get("summary") or "").strip()
        summary_s = f"Summary: {summary} | " if summary else ""
        ts = ev.get("timestamp", "?")
        ts_s = f"{ts:.2f}s" if isinstance(ts, (int, float)) else str(ts)
        return (
            f"Event {i}: {cam_label}[Track {ev.get('track_id', '?')} | t={ts_s}] "
            f"Zone: {ev.get('zone', '?')} | "
            f"{summary_s}"
            f"{ev.get('activity', '?')} | "
            f"Held: {held_s} | "
            f"Pickup: {pickup_s} | "
            f"Conf: {conf_s}"
        )

    @staticmethod
    def _format_legacy(i: int, ev: Dict, cam_label: str = "") -> str:
        meta = ev.get("metadata", {})
        conf = meta.get("confidence", meta.get("conf", "?"))
        conf_s = f"{conf:.2f}" if isinstance(conf, float) else str(conf)
        clip = meta.get("clip_pointer", meta.get("clip", ""))
        return (
            f"Event {i}: {cam_label}[{ev.get('type', '?')}] "
            f"{ev.get('start_time', '?')}–{ev.get('end_time', '?')} | "
            f"Zone: {ev.get('zone', '?')} | "
            f"Conf: {conf_s} | "
            f"clip: {clip}"
        )

    def _format_events(self, events: List[Dict], multi_cam: bool = False) -> str:
        if multi_cam:
            # Group appearance descriptions by (source_video, track_id) so the LLM
            # can cross-reference the same person across cameras by appearance.
            cam_track_desc: Dict[str, Dict[int, str]] = {}
            for ev in events:
                src = ev.get("source_video", "")
                tid = ev.get("track_id")
                desc = (ev.get("description") or "").strip()
                if src and isinstance(tid, int) and desc:
                    cam_track_desc.setdefault(src, {})[tid] = desc

            lines: List[str] = []
            if cam_track_desc:
                lines.append("Identified people (by camera):")
                for src in sorted(cam_track_desc):
                    for tid in sorted(cam_track_desc[src]):
                        lines.append(
                            f"  [{src} Track {tid}]: {cam_track_desc[src][tid]}"
                        )
                lines.append("")

            for i, ev in enumerate(events):
                src = ev.get("source_video", "")
                lbl = f"[{src}] " if src else ""
                if self._is_observation_schema(ev):
                    lines.append(self._format_observation(i, ev, cam_label=lbl))
                else:
                    lines.append(self._format_legacy(i, ev, cam_label=lbl))
            return "\n".join(lines)

        # Single-camera path — collect last description per track.
        track_desc: Dict[int, str] = {}
        for ev in events:
            tid = ev.get("track_id")
            desc = (ev.get("description") or "").strip()
            if isinstance(tid, int) and desc:
                track_desc[tid] = desc

        lines: List[str] = []
        if track_desc:
            lines.append("Identified people:")
            for tid in sorted(track_desc):
                lines.append(f"  Track {tid}: {track_desc[tid]}")
            lines.append("")

        for i, ev in enumerate(events):
            if self._is_observation_schema(ev):
                lines.append(self._format_observation(i, ev))
            else:
                lines.append(self._format_legacy(i, ev))
        return "\n".join(lines)

    def _trim_events(
        self, events: List[Dict], max_chars: int = 2400, multi_cam: bool = False
    ) -> List[Dict]:
        """Return a budget-trimmed subset, prioritising pickup events and context around them."""
        if not events:
            return events
        if len(self._format_events(events, multi_cam=multi_cam)) <= max_chars:
            return events

        # Priority set: pickup events ± 4 context + last event per track (shows final state)
        priority_indices: set[int] = set()
        for i, ev in enumerate(events):
            if ev.get("pickup_confirmed"):
                for j in range(max(0, i - 4), min(len(events), i + 5)):
                    priority_indices.add(j)

        # Always include the most recent observation per track so the LLM sees
        # what the person was ultimately doing (e.g. handling a specific object).
        last_per_track: Dict[int, int] = {}
        for i, ev in enumerate(events):
            tid = ev.get("track_id")
            if isinstance(tid, int):
                last_per_track[tid] = i
        priority_indices.update(last_per_track.values())

        # Build candidate list: priority first, then others in chronological order
        priority = [events[i] for i in sorted(priority_indices)]
        others   = [ev for i, ev in enumerate(events) if i not in priority_indices]

        # Fill up to max_chars
        selected: List[Dict] = []
        for ev in priority + others:
            trial = selected + [ev]
            if len(self._format_events(trial, multi_cam=multi_cam)) > max_chars:
                break
            selected.append(ev)

        # Re-sort by timestamp so the narrative is chronological
        selected.sort(key=lambda e: float(e.get("timestamp") or e.get("time") or 0))
        return selected if selected else events[:1]

    def _run_inference(
        self,
        prompt: str,
        grammar_str: str = "",  # reserved, not used — LlamaGrammar segfaults on parse errors
        max_tokens: int = 512,
        temperature: float = 0.2,
    ) -> str:
        self._load_model()
        result = self._model.create_chat_completion(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        raw = result["choices"][0]["message"]["content"].strip()
        print(f"[LLM raw output] finish_reason={result['choices'][0].get('finish_reason')} len={len(raw)} preview={raw[:200]!r}")
        return raw

    def _parse_json(self, raw: str, fallback: Dict) -> Dict:
        import re
        base = dict(fallback)
        # Strip <think>...</think> blocks some models emit before JSON
        cleaned = re.sub(r"<\|?think(?:ing)?\|?>.*?</\|?think(?:ing)?\|?>", "", raw, flags=re.DOTALL | re.IGNORECASE)
        # Strip markdown code fences
        cleaned = re.sub(r"```(?:json)?\s*", "", cleaned).strip()
        for candidate in (cleaned, raw):
            try:
                return base | json.loads(candidate)
            except (json.JSONDecodeError, ValueError):
                pass
            start = candidate.find("{")
            end = candidate.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return base | json.loads(candidate[start:end])
                except (json.JSONDecodeError, ValueError):
                    pass
        return base

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def summarize_events(self, events: List[Dict]) -> Dict:
        """Return a natural-language summary dict for the given event list."""
        if not events:
            return dict(_SUMMARIZE_FALLBACK) | {"summary": "No events recorded."}

        sources = {ev.get("source_video", "") for ev in events}
        multi_cam = len(sources) > 1 and any(sources)

        trimmed = self._trim_events(events, multi_cam=multi_cam)
        start_t = trimmed[0].get("start_time") or trimmed[0].get("timestamp") or "?"
        end_t = trimmed[-1].get("end_time") or trimmed[-1].get("timestamp") or "?"
        period = f"{start_t}–{end_t}"
        event_log = self._format_events(trimmed, multi_cam=multi_cam)

        # Inject factual pickup roster so even a small model can't miss confirmed pickups.
        pickup_lines: List[str] = []
        seen_keys: set = set()
        for ev in events:
            if ev.get("pickup_confirmed"):
                tid = ev.get("track_id", "?")
                ts = ev.get("timestamp", "?")
                ts_s = f"{ts:.1f}s" if isinstance(ts, (int, float)) else str(ts)
                zone = ev.get("zone", "?")
                items = [
                    _short_item_name(p)
                    for p in (ev.get("picked_up_items") or [])
                    if isinstance(p, dict) and p.get("name")
                ]
                item_s = ", ".join(items) if items else "unidentified item"
                key = f"{tid}-{ts_s}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    pickup_lines.append(f"  - Track {tid} at {ts_s} in zone '{zone}': {item_s}")
        pickup_block = ""
        if pickup_lines:
            pickup_block = (
                "=== CONFIRMED PICKUPS (state each in your summary) ===\n"
                + "\n".join(pickup_lines)
                + "\n=== END CONFIRMED PICKUPS ===\n\n"
            )

        prompt = SUMMARIZE_PROMPT.format(period=period, event_log=pickup_block + event_log)
        raw = self._run_inference(prompt, SUMMARIZE_GRAMMAR, max_tokens=1024)
        return self._parse_json(raw, _SUMMARIZE_FALLBACK)

    def answer_query(self, events: List[Dict], query: str) -> Dict:
        """Answer a natural-language question about the event log."""
        if not events:
            return dict(_QA_FALLBACK) | {"answer": "No events available to query."}

        sources = {ev.get("source_video", "") for ev in events}
        multi_cam = len(sources) > 1 and any(sources)

        trimmed = self._trim_events(events, multi_cam=multi_cam)
        event_log = self._format_events(trimmed, multi_cam=multi_cam)
        prompt = QA_PROMPT.format(event_log=event_log, query=query)
        raw = self._run_inference(prompt, QA_GRAMMAR, max_tokens=1024)
        return self._parse_json(raw, _QA_FALLBACK)

    def generate_alert(self, event: Dict) -> Dict:
        """Generate a short alert dict for a single suspicious event."""
        event_str = self._format_events([event])
        prompt = ALERT_PROMPT.format(event=event_str)
        raw = self._run_inference(prompt, ALERT_GRAMMAR, max_tokens=256)
        return self._parse_json(raw, _ALERT_FALLBACK)


# ---------------------------------------------------------------------------
# MiniCPM-V-backed text reasoner (reuses the already-loaded VLM weights)
# ---------------------------------------------------------------------------


class MiniCPMTextReasoner(Reasoner):
    """Text-only reasoner backed by a standalone MiniCPM language model.

    Two performance modes:
      NORMAL  — MiniCPM5-1B  (fast, low VRAM)
      BOOSTED — MiniCPM4.1-8B (higher quality, more VRAM)

    Selected via the EYAS_LLM_MODE env var (default: "normal").
    """

    NORMAL = "normal"
    BOOSTED = "boosted"

    REPOS: Dict[str, str] = {
        NORMAL: "openbmb/MiniCPM5-1B",
        BOOSTED: "openbmb/MiniCPM4.1-8B",
    }

    def __init__(
        self,
        mode: str = NORMAL,
        device: Optional[str] = None,
        dtype: str = "auto",
    ) -> None:
        if mode not in self.REPOS:
            raise ValueError(
                f"Unknown LLM mode {mode!r}. Choose 'normal' or 'boosted'."
            )
        self._model_path = self.REPOS[mode]
        self._n_ctx = 0
        self._n_gpu_layers = 0
        self._model = None
        self.mode = mode
        self.device = device
        self.dtype = dtype
        self._hf_model = None
        self._tokenizer = None
        self._loaded = False

    def _load_model(self) -> None:
        if self._loaded:
            return
        import torch

        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "transformers is required for MiniCPMTextReasoner. "
                "Run: pip install transformers"
            ) from exc
        repo = self.REPOS[self.mode]
        self._tokenizer = AutoTokenizer.from_pretrained(repo, trust_remote_code=True)
        torch_dtype = getattr(torch, self.dtype) if self.dtype != "auto" else "auto"
        self._hf_model = AutoModelForCausalLM.from_pretrained(
            repo,
            torch_dtype=torch_dtype,
            trust_remote_code=True,
        )
        if self.device:
            self._hf_model = self._hf_model.to(self.device)
        self._hf_model.eval()
        self._loaded = True

    def _run_inference(
        self,
        prompt: str,
        grammar_str: str,
        max_tokens: int = 512,
        temperature: float = 0.2,
    ) -> str:
        import re

        self._load_model()
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        input_ids = self._tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to(next(self._hf_model.parameters()).device)
        pad_id = (
            self._tokenizer.pad_token_id
            if self._tokenizer.pad_token_id is not None
            else self._tokenizer.eos_token_id
        )
        gen_kwargs: Dict = {
            "max_new_tokens": max_tokens,
            "do_sample": temperature > 0,
            "pad_token_id": pad_id,
        }
        if temperature > 0:
            gen_kwargs["temperature"] = temperature
        gen = self._hf_model.generate(input_ids, **gen_kwargs)
        trimmed = gen[:, input_ids.shape[1] :]
        text = self._tokenizer.batch_decode(trimmed, skip_special_tokens=True)[
            0
        ].strip()
        # Strip Qwen3.5-style thinking block if present before the JSON
        text = re.sub(r"<think>.*?</think>\s*", "", text, flags=re.DOTALL)
        return text
