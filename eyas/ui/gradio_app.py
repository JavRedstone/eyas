"""Eyas Gradio backend — pure API server, React SPA frontend.

All gr.* components are hidden; they exist only to register API endpoints.
The React frontend (ui/dist/) is served by app.py at GET /.
"""

import io
import json
import sys
import threading
import traceback
import time as _time_mod
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_RUNS_DIR = _DATA_DIR / "runs"

_EYAS_ROOT = str(Path(__file__).resolve().parents[1])
_UI_ROOT = str(Path(__file__).resolve().parent)
if sys.path and str(Path(sys.path[0]).resolve()) == _UI_ROOT:
    sys.path.pop(0)
if _EYAS_ROOT not in sys.path:
    sys.path.insert(0, _EYAS_ROOT)

import gradio as gr

try:
    import spaces as _spaces
except Exception:
    _spaces = None


def _gpu(fn=None, **kwargs):
    if _spaces is None:
        if fn is None:
            def _decorator(inner):
                return inner
            return _decorator
        return fn
    if fn is None:
        return _spaces.GPU(**kwargs)
    return _spaces.GPU(fn)

from storage import manager as storage
import model_registry as _mreg
from ui.locale import (
    LANGUAGE_LABELS,
    SPLASH_MODEL_KEYS,
    Strings,
    format_event_row,
    format_translation_time,
    localize_llm_result,
    localize_text,
    pipeline_steps_default,
)

_mreg.start()

_SAMPLES_DIR = Path(__file__).parent.parent / "input"
_SAMPLE_PATHS: Dict[str, str] = {
    p.stem: str(p) for p in sorted(_SAMPLES_DIR.glob("*.mp4"))
}

# ── Session state (accumulates across multiple video runs) ────────────────────
_session_lock = threading.Lock()
_session: Dict = {"runs": [], "events": []}

# ── Active pipeline tracking (for clean stop/restart on MPS) ─────────────────
_pipeline_lock = threading.Lock()
_active_stop_event: Optional[threading.Event] = None
_active_pipeline_thread: Optional[threading.Thread] = None


def _session_append_run(run_id: str, video_name: str, output_dir: str,
                         events: list, summary: dict, annotated_video_path: str) -> None:
    tagged = [{**e, "source_video": video_name} for e in events]
    with _session_lock:
        _session["events"].extend(tagged)
        _session["runs"].append({
            "run_id": run_id,
            "video_name": video_name,
            "output_dir": output_dir,
            "annotated_video_path": annotated_video_path,
            "summary": summary,
        })


def _session_clear() -> None:
    with _session_lock:
        _session["runs"].clear()
        _session["events"].clear()


def _session_export_zip() -> dict:
    import base64
    with _session_lock:
        runs = list(_session["runs"])
        all_events = list(_session["events"])

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("all_events.json", json.dumps(all_events, indent=2))
        for run in runs:
            prefix = run["run_id"]
            run_events = [e for e in all_events if e.get("source_video") == run["video_name"]]
            zf.writestr(f"{prefix}/events.json", json.dumps(run_events, indent=2))
            summary = run.get("summary")
            if summary:
                text = summary.get("summary", "") if isinstance(summary, dict) else str(summary)
                zf.writestr(f"{prefix}/summary.txt", text)
            ann = run.get("annotated_video_path")
            if ann and Path(ann).exists():
                zf.write(ann, f"{prefix}/{Path(ann).name}")

    return {"data": base64.b64encode(buf.getvalue()).decode()}



def build_app(
    language: str = "en",
    prefs_path: Optional[Path] = None,
) -> gr.Blocks:

    S = Strings(language)
    _lang = [language]  # mutable so save_language can hot-swap at runtime

    # ── API functions (closures so they can access S, _lang, prefs_path) ──

    def poll_splash() -> dict:
        """Return model loading state for the splash screen."""
        from model_registry import get_states
        states = get_states()
        done = _mreg.all_done()
        total = len(states)
        done_count = sum(1 for s in states if s.status in {"ready", "error", "skipped"})
        progress_pct = int(done_count / total * 100) if total else 0

        registry_keys = ["yolo", "vlm", "llm", "tts", "tinyaya"]
        items = []
        for i, s in enumerate(states):
            reg_key = registry_keys[i] if i < len(registry_keys) else ""
            msg_key = SPLASH_MODEL_KEYS.get(reg_key)
            label = S.t(msg_key) if msg_key else s.label
            items.append({
                "label": label,
                "status": s.status,
                "detail": s.detail or "",
                "model_name": s.model_name or "",
            })
        return {"done": done, "states": items, "progress_pct": progress_pct, "language_label": LANGUAGE_LABELS.get(_lang[0], "English")}

    @_gpu(duration=300)
    def run_pipeline(video_path: str):
        """Streaming pipeline — yields JSON update objects."""
        import time as _time
        from visual_pipeline import run_visual_pipeline
        from postprocessing.translate_tts import TranslateStats

        steps = [{"id": sid, "state": "pending", "detail": ""} for sid, _, _ in pipeline_steps_default()]
        step_start: dict = {}
        text_cache: dict = {}
        translation_stats = TranslateStats()
        live_events: list = []
        live_rows: list = []
        _progress_done = [0]
        _progress_total = [0]

        def _elapsed(idx: int) -> str:
            if idx not in step_start:
                return ""
            secs = int(_time.time() - step_start[idx])
            m, s = divmod(secs, 60)
            return f"{m}:{s:02d}"

        def _annotate_steps():
            out = []
            for i, step in enumerate(steps):
                detail = step["detail"]
                if step["state"] == "running" and i in step_start:
                    e = _elapsed(i)
                    detail = f"{detail} · {e}" if detail else e
                out.append({**step, "detail": detail})
            return out

        def _emit(status: str, update_type: str = "progress") -> dict:
            done = _progress_done[0]
            total = _progress_total[0]
            progress_pct = int((done / total) * 100) if total else 0
            return {
                "type": update_type,
                "status": status,
                "steps": _annotate_steps(),
                "events": list(live_events),
                "rows": list(live_rows),
                "progress_done": done,
                "progress_total": total,
                "progress_pct": progress_pct,
                "video_name": Path(video_path).name,
            }

        def _start_step(idx: int, step_id: str, detail: str = "") -> None:
            step_start[idx] = _time.time()
            steps[idx] = {"id": step_id, "state": "running", "detail": detail}

        def _finish_step(idx: int, step_id: str, detail: str = "") -> None:
            step_start.pop(idx, None)
            steps[idx] = {"id": step_id, "state": "done", "detail": detail}

        if video_path is None:
            steps[0]["state"] = "error"
            steps[0]["detail"] = S.t("status.no_video_selected")
            yield _emit(S.t("status.no_video"), "error")
            return

        import queue as _queue
        import threading as _threading

        # Cancel any previous pipeline run and wait for it to fully exit.
        # Without this, the old thread may still be executing VLM inference on
        # MPS when the new run calls offload_vlm(), causing a Metal command
        # encoder conflict that aborts the process.
        global _active_stop_event, _active_pipeline_thread
        with _pipeline_lock:
            _prev_stop = _active_stop_event
            _prev_thread = _active_pipeline_thread
        if _prev_stop is not None:
            _prev_stop.set()
        if _prev_thread is not None and _prev_thread.is_alive():
            _prev_thread.join(timeout=15.0)

        _start_step(0, "load_video")
        yield _emit(S.t("status.loading_video"))

        _finish_step(0, "load_video", Path(video_path).name)
        _start_step(1, "yolo", S.t("pipeline.starting"))
        steps[2] = {"id": "vlm", "state": "pending", "detail": ""}
        yield _emit(S.t("status.running_yolo"))

        run_id = _time_mod.strftime("%Y%m%d_%H%M%S")
        output_dir = str(_RUNS_DIR / run_id)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        _q: _queue.Queue = _queue.Queue()
        _last_progress_t = [0.0]

        def _on_progress(
            done: int,
            total: int,
            track_count: int,
            vlm_fired: bool,
            _=None,
        ) -> None:
            now = _time.time()
            if vlm_fired or now - _last_progress_t[0] >= 0.2:
                _q.put(("progress", done, total, track_count, vlm_fired))
                _last_progress_t[0] = now

        def _on_new_events(evs: list) -> None:
            for ev in evs:
                i = len(live_events)
                live_events.append(ev)
                row = format_event_row(ev, i, S, text_cache=text_cache, stats=translation_stats)
                live_rows.append(row)

        _stop_event = _threading.Event()
        with _pipeline_lock:
            _active_stop_event = _stop_event

        def _run() -> None:
            try:
                result = run_visual_pipeline(
                    video_path=video_path,
                    output_dir=output_dir,
                    write_annotated_video=True,
                    progress=_on_progress,
                    on_event=_on_new_events,
                    preloaded_tracker=_mreg.get("yolo"),
                    preloaded_vlm=_mreg.get("vlm"),
                    locale=_lang[0],
                    stop_event=_stop_event,
                )
                _q.put(("done", result))
            except Exception as exc:
                _q.put(("error", f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"))

        _vp_thread = _threading.Thread(target=_run, daemon=True)
        with _pipeline_lock:
            _active_pipeline_thread = _vp_thread
        _vp_thread.start()

        _model_loaded = False
        try:
            while True:
                try:
                    msg = _q.get(timeout=1.0)
                except _queue.Empty:
                    if not _model_loaded:
                        steps[1]["detail"] = S.t("pipeline.loading_weights")
                        steps[2]["detail"] = S.t("pipeline.loading_weights")
                        steps[2]["state"] = "running"
                    yield _emit(S.t("status.loading_models") if not _model_loaded else S.t("status.processing"))
                    continue

                kind = msg[0]
                if kind == "progress":
                    if not _model_loaded:
                        _model_loaded = True
                        step_start[1] = _time.time()
                    _, done, total, track_count, vlm_fired = msg
                    _progress_done[0] = int(done or 0)
                    _progress_total[0] = int(total or 0)
                    pct = f"{done}/{total}" if total else str(done)
                    person_key = "pipeline.persons" if track_count == 1 else "pipeline.persons_plural"
                    person_s = S.t(person_key, count=track_count)
                    steps[1] = {"id": "yolo", "state": "running", "detail": f"{S.t('pipeline.frame', pct=pct)} · {person_s}"}
                    if vlm_fired:
                        if 2 not in step_start:
                            step_start[2] = _time.time()
                        steps[2] = {"id": "vlm", "state": "running", "detail": S.t("pipeline.frame", pct=pct)}
                    yield _emit(S.t("status.processing_frame", pct=pct))
                elif kind == "done":
                    vp = msg[1]
                    break
                else:
                    steps[1] = {"id": "yolo", "state": "error", "detail": str(msg[1])[:80]}
                    steps[2] = {"id": "vlm", "state": "error", "detail": ""}
                    yield _emit(S.t("status.pipeline_error", error=msg[1]), "error")
                    return
        finally:
            # Signal the pipeline thread to stop (idempotent if already done).
            # This fires whether we exit normally, via return/break, or via
            # GeneratorExit (Gradio cancelling the generator on stop).
            _stop_event.set()

        events: List[Dict] = vp.events
        _finish_step(1, "yolo", S.t("pipeline.frames_tracks", frames=vp.frames_processed, tracks=vp.unique_tracks))
        _finish_step(2, "vlm", S.t("pipeline.events_count", count=len(events)))

        # VLM is done — free its GPU memory so TTS and the LLM have more VRAM.
        _mreg.offload_vlm()

        _start_step(3, "llm_summarize")

        rows = [
            format_event_row(ev, i, S, text_cache=text_cache, stats=translation_stats)
            for i, ev in enumerate(events)
        ]
        live_rows.clear()
        live_rows.extend(rows)

        zone_counts: dict = {}
        for ev in events:
            z = ev.get("zone", "").strip().lower().replace(" ", "_")
            if z:
                zone_counts[z] = zone_counts.get(z, 0) + 1

        yield {**_emit(S.t("status.running_llm")),
               "zone_counts": zone_counts, "output_dir": output_dir}

        # LLM step — run in a thread so we can yield timer ticks
        _llm_q: _queue.Queue = _queue.Queue()

        def _run_llm():
            try:
                _r = _mreg.get("llm")
                if _r is None:
                    raise RuntimeError("LLM not available")
                _llm_q.put(("done", _r.summarize_events(events)))
            except Exception as exc:
                _llm_q.put(("error", str(exc)))

        _threading.Thread(target=_run_llm, daemon=True).start()

        while True:
            try:
                llm_msg = _llm_q.get(timeout=1.0)
                if llm_msg[0] == "done":
                    llm = llm_msg[1]
                else:
                    llm = {"summary": S.t("status.llm_unavailable"), "flags": [], "suspicious_clips": [], "risk_level": "none"}
                break
            except _queue.Empty:
                yield {**_emit(S.t("status.running_llm")),
                       "zone_counts": zone_counts, "output_dir": output_dir}

        llm_display, llm_stats = localize_llm_result(llm, _lang[0])
        combined_stats = translation_stats
        if llm_stats:
            combined_stats = combined_stats.merge(llm_stats)
        translation_time_str = format_translation_time(
            S,
            combined_stats if (combined_stats.cache_hits or combined_stats.cache_misses) else None,
        )

        risk_key = llm.get("risk_level", "none")
        _finish_step(3, "llm_summarize", S.t("pipeline.risk", level=S.risk_label(risk_key)))
        status = S.t("status.done", frames=vp.frames_processed, tracks=vp.unique_tracks, events=len(events))
        if translation_time_str:
            status = f"{status}  ·  {translation_time_str}"

        ann_vid_path = vp.annotated_video_path
        _progress_done[0] = int(vp.frames_processed or _progress_done[0])
        _progress_total[0] = int(vp.frames_processed or _progress_total[0] or _progress_done[0])

        video_name = Path(video_path).name
        _session_append_run(run_id, video_name, output_dir, events, llm_display, ann_vid_path)

        yield {
            "type": "final",
            "status": status,
            "steps": _annotate_steps(),
            "events": events,
            "video_name": video_name,
            "rows": rows,
            "summary": llm_display["summary"],
            "translation_time": translation_time_str,
            "risk_level": risk_key,
            "flags": llm_display.get("flags", []),
            "suspicious_clips": llm.get("suspicious_clips", []),
            "zone_counts": zone_counts,
            "annotated_video_path": ann_vid_path,
            "output_dir": output_dir,
        }

    @_gpu(duration=120)
    def ask_footage(message: str, history: list, events: list) -> tuple:
        def _append(hist, user_msg, assistant_msg):
            return hist + [
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": assistant_msg},
            ]

        if not message.strip():
            return history, "", ""
        if not events:
            reply = S.t("status.no_events_qa")
            return _append(history, message, reply), "", ""
        try:
            _r = _mreg.get("llm")
            if _r is None:
                reply = S.t("status.llm_unavailable")
                return _append(history, message, reply), "", ""
            result = _r.answer_query(events, message)
            reply = result["answer"]
            reply, stats = localize_text(reply, _lang[0])
            if result.get("clips"):
                reply += "\n\n" + S.t("status.related_clips", clips=", ".join(result["clips"]))
            timing = format_translation_time(S, stats)
        except Exception as exc:
            reply = S.t("status.llm_error", error=f"{type(exc).__name__}: {exc}")
            timing = ""
        return _append(history, message, reply), "", timing

    @_gpu(duration=120)
    def generate_audio(events: list) -> tuple:
        import numpy as np
        if not events:
            return None, S.t("status.no_events_qa")
        _r = _mreg.get("llm")
        if _r is None:
            return None, S.t("status.llm_unavailable")
        # Offload VLM to free VRAM before loading TTS, then ensure TTS is loaded.
        _mreg.load_tts_on_demand()
        try:
            llm = _r.summarize_events(events)
            text = llm.get("summary", "").strip()
            if not text:
                return None, "No summary to speak."
            text, stats = localize_text(text, _lang[0])
            from postprocessing.translate_tts import tts
            chunks = list(tts(text, target_lang=S.tts_lang))
            if not chunks:
                return None, "TTS produced no audio."
            sample_rate = chunks[0][0]
            audio = np.concatenate([c[1] for c in chunks])
            timing = format_translation_time(S, stats)
            return (sample_rate, audio), timing or "Done."
        except Exception as exc:
            return None, f"Audio error: {type(exc).__name__}: {exc}"

    def get_samples() -> list:
        return list(_SAMPLE_PATHS.keys())

    def load_sample(name: str):
        path = _SAMPLE_PATHS.get(name)
        if path is None:
            return None
        return path

    def refresh_library() -> list:
        return storage.choices(_lang[0])

    def preview_clip(choice: str):
        path = storage.path_from_choice(choice) if choice else None
        return path

    def load_clip_for_analysis(choice: str) -> tuple:
        path = storage.path_from_choice(choice) if choice else None
        if path is None:
            return None, S.t("status.clip_not_found")
        return path, S.t("status.loaded_clip", choice=choice)

    def delete_clip(choice: str) -> tuple:
        if not choice:
            return S.t("status.nothing_selected"), storage.choices(_lang[0])
        filename = choice.split(" — ", 1)[1].split("  ")[0].strip() if " — " in choice else ""
        ok = storage.delete(filename) if filename else False
        msg = S.t("status.deleted", filename=filename) if ok else S.t("status.delete_failed")
        return msg, storage.choices(_lang[0])

    def load_event_clip(clip_index: int, output_dir: str):
        import cv2 as _cv2, tempfile as _tf, json as _json
        if not output_dir:
            return None
        p = Path(output_dir)

        # Load events to get timestamp
        events_file = p / "events.json"
        if not events_file.exists():
            return None
        events_data = _json.loads(events_file.read_text())
        if clip_index >= len(events_data):
            return None
        ev = events_data[clip_index]
        ts = float(ev.get("timestamp") or ev.get("time") or 0.0)

        # Find the annotated video
        video_path = next(p.glob("*_annotated.mp4"), None) or next(p.glob("*.mp4"), None)
        if not video_path:
            return None

        cap = _cv2.VideoCapture(str(video_path))
        fps = cap.get(_cv2.CAP_PROP_FPS) or 24.0
        w   = int(cap.get(_cv2.CAP_PROP_FRAME_WIDTH))
        h   = int(cap.get(_cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(_cv2.CAP_PROP_FRAME_COUNT))

        # Extract 2s before → 4s after the event
        start_f = max(0, int((ts - 2.0) * fps))
        end_f   = min(total_frames, int((ts + 4.0) * fps))

        cap.set(_cv2.CAP_PROP_POS_FRAMES, start_f)
        tmp = _tf.NamedTemporaryFile(suffix=".mp4", delete=False,
                                     prefix=f"eyas_clip_{clip_index}_")
        tmp.close()
        fourcc = _cv2.VideoWriter_fourcc(*"avc1")
        writer = _cv2.VideoWriter(tmp.name, fourcc, fps, (w, h))
        for _ in range(end_f - start_f):
            ok, frame = cap.read()
            if not ok:
                break
            writer.write(frame)
        writer.release()
        cap.release()
        return tmp.name

    def load_flagged_clip(clip_name: str, output_dir: str):
        if not clip_name or not output_dir:
            return None
        p = Path(output_dir) / clip_name
        if p.is_file():
            return str(p)
        ann = next((f for f in Path(output_dir).glob("*.mp4")), None)
        return str(ann) if ann else None

    def save_language(lang_label: str) -> str:
        nonlocal S
        if prefs_path is None:
            return S.t("status.no_prefs_path")
        lang_key = next((k for k, v in LANGUAGE_LABELS.items() if v == lang_label), None)
        if lang_key is None:
            lang_key = lang_label if lang_label in LANGUAGE_LABELS else "en"
        try:
            existing = {}
            try:
                existing = json.loads(prefs_path.read_text())
            except Exception:
                pass
            prefs_path.write_text(json.dumps({**existing, "language": lang_key}, indent=2))
            _lang[0] = lang_key
            S = Strings(lang_key)
            return S.t("status.language_saved", language=lang_label)
        except Exception as exc:
            return S.t("status.prefs_error", error=exc)

    # ── Gradio Blocks — minimal hidden components for API endpoints ──────────

    with gr.Blocks(title=S.t("app.title")) as demo:

        with gr.Group(visible=False):

            # Splash polling
            gr.Button("_").click(poll_splash, outputs=[gr.JSON()], api_name="poll_splash")

            # Pipeline streaming — gr.Textbox so the client passes the path string directly
            _vid_path = gr.Textbox()
            _pipe_out = gr.JSON()
            gr.Button("_").click(run_pipeline, inputs=[_vid_path], outputs=[_pipe_out], api_name="run_pipeline")

            # QA
            _msg = gr.Textbox()
            _hist = gr.JSON()
            _evts = gr.JSON()
            _qa_hist = gr.JSON()
            _qa_empty = gr.Textbox()
            _qa_timing = gr.Textbox()
            gr.Button("_").click(
                ask_footage, inputs=[_msg, _hist, _evts],
                outputs=[_qa_hist, _qa_empty, _qa_timing],
                api_name="ask_footage",
            )

            # Audio generation
            _evts2 = gr.JSON()
            _audio_out = gr.Audio()
            _audio_status = gr.Textbox()
            gr.Button("_").click(
                generate_audio, inputs=[_evts2],
                outputs=[_audio_out, _audio_status],
                api_name="generate_audio",
            )

            # Sample list
            gr.Button("_").click(get_samples, outputs=[gr.JSON()], api_name="get_samples")

            # Load sample video — Textbox so client receives plain path string
            _sample_name = gr.Textbox()
            _sample_path_out = gr.Textbox()
            gr.Button("_").click(load_sample, inputs=[_sample_name], outputs=[_sample_path_out], api_name="load_sample")

            # Clip library ops
            gr.Button("_").click(refresh_library, outputs=[gr.JSON()], api_name="refresh_library")

            _choice1 = gr.Textbox()
            _preview_vid = gr.Video()
            gr.Button("_").click(preview_clip, inputs=[_choice1], outputs=[_preview_vid], api_name="preview_clip")

            _choice2 = gr.Textbox()
            _loaded_vid = gr.Video()
            _loaded_status = gr.Textbox()
            gr.Button("_").click(
                load_clip_for_analysis, inputs=[_choice2],
                outputs=[_loaded_vid, _loaded_status],
                api_name="load_clip_for_analysis",
            )

            _choice3 = gr.Textbox()
            _del_msg = gr.Textbox()
            _del_choices = gr.JSON()
            gr.Button("_").click(
                delete_clip, inputs=[_choice3],
                outputs=[_del_msg, _del_choices],
                api_name="delete_clip",
            )

            # Event clip preview
            _ci = gr.Number()
            _od = gr.Textbox()
            _ec_vid = gr.Video()
            gr.Button("_").click(load_event_clip, inputs=[_ci, _od], outputs=[_ec_vid], api_name="load_event_clip")

            # Flagged clip preview
            _cn = gr.Textbox()
            _od2 = gr.Textbox()
            _fc_vid = gr.Video()
            gr.Button("_").click(load_flagged_clip, inputs=[_cn, _od2], outputs=[_fc_vid], api_name="load_flagged_clip")

            # Save language
            _lang_in = gr.Textbox()
            _lang_out = gr.Textbox()
            gr.Button("_").click(save_language, inputs=[_lang_in], outputs=[_lang_out], api_name="save_language")

            # Session management
            def clear_session() -> str:
                _session_clear()
                return "cleared"

            def export_session_zip() -> str:
                return _session_export_zip()

            gr.Button("_").click(clear_session, outputs=[gr.Textbox()], api_name="clear_session")

            gr.Button("_").click(export_session_zip, outputs=[gr.JSON()], api_name="export_session_zip")

    return demo
