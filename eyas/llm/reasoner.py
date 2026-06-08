"""LLM reasoning wrapper using llama-cpp-python for local inference."""

from __future__ import annotations

import json
import os
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
    "summary": "",
    "flags": [],
    "suspicious_clips": [],
    "risk_level": "none",
}
_QA_FALLBACK: Dict = {"answer": "", "relevant_event_indices": [], "clips": []}
_ALERT_FALLBACK: Dict = {"alert": "", "severity": "low", "clip": ""}


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
        if not os.path.isfile(self._model_path):
            raise RuntimeError(
                f"Model file not found: {self._model_path!r}. "
                "Download a Nemotron GGUF and set EYAS_MODEL_PATH or place it at "
                "the default path."
            )
        try:
            from llama_cpp import Llama  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "llama-cpp-python is not installed. Run: pip install llama-cpp-python"
            ) from exc

        self._model = Llama(
            model_path=self._model_path,
            n_ctx=self._n_ctx,
            n_gpu_layers=self._n_gpu_layers,
            verbose=False,
        )

    @staticmethod
    def _is_observation_schema(ev: Dict) -> bool:
        """True for ObservationEvent dicts (structurer output); False for legacy dicts."""
        return "timestamp" in ev and "activity" in ev and "track_id" in ev

    @staticmethod
    def _format_observation(i: int, ev: Dict) -> str:
        conf = ev.get("confidence", "?")
        conf_s = f"{conf:.2f}" if isinstance(conf, float) else str(conf)
        held = ev.get("held_objects") or []
        held_s = ", ".join(f"{h['name']} x{h.get('count',1)}" for h in held) if held else "-"
        pickup = ev.get("pickup_confirmed", False)
        picked = ev.get("picked_up_items") or []
        pickup_s = ("YES -> " + ", ".join(f"{p['name']} x{p.get('count',1)}" for p in picked)) if pickup else "no"
        return (
            f"Event {i}: [Track {ev.get('track_id','?')} | t={ev.get('timestamp','?'):.2f}s] "
            f"Zone: {ev.get('zone','?')} | "
            f"{ev.get('activity','?')} | "
            f"Held: {held_s} | "
            f"Pickup: {pickup_s} | "
            f"Conf: {conf_s}"
        )

    @staticmethod
    def _format_legacy(i: int, ev: Dict) -> str:
        meta = ev.get("metadata", {})
        conf = meta.get("confidence", meta.get("conf", "?"))
        conf_s = f"{conf:.2f}" if isinstance(conf, float) else str(conf)
        clip = meta.get("clip_pointer", meta.get("clip", ""))
        return (
            f"Event {i}: [{ev.get('type', '?')}] "
            f"{ev.get('start_time', '?')}–{ev.get('end_time', '?')} | "
            f"Zone: {ev.get('zone', '?')} | "
            f"Conf: {conf_s} | "
            f"clip: {clip}"
        )

    def _format_events(self, events: List[Dict]) -> str:
        lines: List[str] = []
        for i, ev in enumerate(events):
            if self._is_observation_schema(ev):
                lines.append(self._format_observation(i, ev))
            else:
                lines.append(self._format_legacy(i, ev))
        return "\n".join(lines)

    def _trim_events(self, events: List[Dict], max_chars: int = 3000) -> List[Dict]:
        """Return as many trailing events as fit within max_chars when formatted."""
        if not events:
            return events
        formatted = self._format_events(events)
        if len(formatted) <= max_chars:
            return events
        # Drop from the front until it fits
        for start in range(1, len(events)):
            if len(self._format_events(events[start:])) <= max_chars:
                return events[start:]
        return events[-1:]

    def _run_inference(
        self,
        prompt: str,
        grammar_str: str,
        max_tokens: int = 512,
        temperature: float = 0.2,
    ) -> str:
        self._load_model()
        try:
            from llama_cpp import LlamaGrammar  # type: ignore
            grammar = LlamaGrammar.from_string(grammar_str, verbose=False)
        except Exception:
            grammar = None

        full_prompt = f"System: {SYSTEM_PROMPT}\n\nUser: {prompt}\nAssistant:"
        result = self._model(
            full_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["```", "User:", "Question:"],
            grammar=grammar,
        )
        return result["choices"][0]["text"].strip()

    def _parse_json(self, raw: str, fallback: Dict) -> Dict:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Try to extract the first {...} block if the model added extra text
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(raw[start:end])
                except json.JSONDecodeError:
                    pass
        return dict(fallback)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def summarize_events(self, events: List[Dict]) -> Dict:
        """Return a natural-language summary dict for the given event list."""
        if not events:
            return dict(_SUMMARIZE_FALLBACK) | {"summary": "No events recorded."}

        trimmed = self._trim_events(events)
        start_t = trimmed[0].get("start_time", "?")
        end_t = trimmed[-1].get("end_time", "?")
        period = f"{start_t}–{end_t}"
        event_log = self._format_events(trimmed)

        prompt = SUMMARIZE_PROMPT.format(period=period, event_log=event_log)
        raw = self._run_inference(prompt, SUMMARIZE_GRAMMAR)
        return self._parse_json(raw, _SUMMARIZE_FALLBACK)

    def answer_query(self, events: List[Dict], query: str) -> Dict:
        """Answer a natural-language question about the event log."""
        if not events:
            return dict(_QA_FALLBACK) | {"answer": "No events available to query."}

        trimmed = self._trim_events(events)
        event_log = self._format_events(trimmed)
        prompt = QA_PROMPT.format(event_log=event_log, query=query)
        raw = self._run_inference(prompt, QA_GRAMMAR)
        return self._parse_json(raw, _QA_FALLBACK)

    def generate_alert(self, event: Dict) -> Dict:
        """Generate a short alert dict for a single suspicious event."""
        event_str = self._format_events([event])
        prompt = ALERT_PROMPT.format(event=event_str)
        raw = self._run_inference(prompt, ALERT_GRAMMAR, max_tokens=256)
        return self._parse_json(raw, _ALERT_FALLBACK)


# ---------------------------------------------------------------------------
# Module-level singleton + convenience shims (backward-compatible API)
# ---------------------------------------------------------------------------

_default_reasoner: Optional[Reasoner] = None


def _get_reasoner() -> Reasoner:
    global _default_reasoner
    if _default_reasoner is None:
        model_path = os.getenv("EYAS_MODEL_PATH", "models/nemotron-nano-4b.gguf")
        n_gpu_layers = int(os.getenv("EYAS_GPU_LAYERS", "-1"))
        _default_reasoner = Reasoner(model_path, n_gpu_layers=n_gpu_layers)
    return _default_reasoner


def summarize_events(events: List[Dict]) -> Dict:
    """Return a natural-language summary dict for the given event list."""
    return _get_reasoner().summarize_events(events)


def answer_query(events: List[Dict], query: str) -> Dict:
    """Answer a natural-language question about the event log."""
    return _get_reasoner().answer_query(events, query)
