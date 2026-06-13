"""Runnable visual pipeline: video -> YOLO tracks -> MiniCPM-V event log."""

from __future__ import annotations

import inspect
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional

import cv2

from event_structuring.structurer import EventStructurer, PersonStatus, Zone
from object_detection.detector import PersonTracker, Track
from video_processing.process import LlamaCppMiniCPMVLM, MiniCPMVLM
from utils.device import get_device
from utils.overlay_text import OverlayLabels
from utils.paths import models_dir
from utils.video import create_video_writer, get_video_info

_DEFAULT_YOLO_WEIGHTS = str(models_dir() / "yolo11n.pt")


@dataclass
class VisualPipelineResult:
    video_path: str
    events_path: str
    annotated_video_path: Optional[str]
    frames_processed: int
    unique_tracks: int
    events: List[dict]

    def summary(self) -> str:
        return (
            f"Processed {self.frames_processed} frames, tracked "
            f"{self.unique_tracks} people, and recorded "
            f"{len(self.events)} MiniCPM-V observations."
        )


def full_frame_zone(width: int, height: int, name: str = "review_area") -> Zone:
    """Full-frame zone covering the entire video."""
    return Zone(name=name, bbox=(0, 0, width, height), kind="shelf")


def _zone_from_filename(stem: str, width: int, height: int) -> Optional[Zone]:
    """Parse zone from filename pattern YYYYMMDD_HHMMSS_<zone_name>.

    Returns a full-frame Zone with the parsed name, or None if the filename
    does not match the convention.
    """
    parts = stem.split("_")
    if (
        len(parts) >= 3
        and len(parts[0]) == 8 and parts[0].isdigit()
        and len(parts[1]) == 6 and parts[1].isdigit()
    ):
        zone_name = "_".join(parts[2:])
        return full_frame_zone(width, height, name=zone_name)
    return None


_ALERT_COLOR  = (0, 0, 220)   # red   (BGR) — suspicious / pickup
_OBSERVE_COLOR = (0, 140, 255) # orange (BGR) — under observation
_NORMAL_COLOR  = (0, 200, 60)  # green  (BGR) — normal track


def _draw_alert_highlight(
    frame,
    x1: int, y1: int, x2: int, y2: int,
    label: str = "SUSPICIOUS",
    frame_idx: int = 0,
) -> None:
    """Red pulsing box with L-corner markers and an alert label banner."""
    pulse = (frame_idx // 10) % 2
    thickness = 4 + pulse * 2

    cv2.rectangle(frame, (x1, y1), (x2, y2), _ALERT_COLOR, thickness)

    # L-shaped corner markers for visual impact
    L = max(12, min(28, (x2 - x1) // 5, (y2 - y1) // 5))
    t = thickness + 1
    for cx, cy, dx, dy in [(x1, y1, 1, 1), (x2, y1, -1, 1), (x1, y2, 1, -1), (x2, y2, -1, -1)]:
        cv2.line(frame, (cx, cy), (cx + dx * L, cy), _ALERT_COLOR, t)
        cv2.line(frame, (cx, cy), (cx, cy + dy * L), _ALERT_COLOR, t)

    # Label banner above the box
    font, scale, ft = cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2
    text = f"!! {label}"
    (tw, th), bl = cv2.getTextSize(text, font, scale, ft)
    lx1, lx2 = max(0, x1), max(0, x1) + tw + 10
    ly2 = max(th + bl + 6, y1)
    ly1 = ly2 - th - bl - 6
    cv2.rectangle(frame, (lx1, ly1), (lx2, ly2), _ALERT_COLOR, -1)
    cv2.putText(frame, text, (lx1 + 5, ly2 - bl - 2), font, scale,
                (255, 255, 255), ft, cv2.LINE_AA)


def draw_tracks(
    frame,
    tracks: List[Track],
    zones: List[Zone],
    statuses: Optional[Dict[int, PersonStatus]] = None,
    labels: Optional[OverlayLabels] = None,
):
    """Draw YOLO person tracks with alert highlighting for suspicious activity."""
    rendered = frame.copy()
    for track in tracks:
        x1, y1, x2, y2 = track.bbox
        status = statuses.get(track.track_id) if statuses else None
        if status and status.confirmed_pickups:
            _draw_alert_highlight(rendered, x1, y1, x2, y2, "SUSPICIOUS")
        elif status and status.observations > 0:
            cv2.rectangle(rendered, (x1, y1), (x2, y2), _OBSERVE_COLOR, 3)
        else:
            cv2.rectangle(rendered, (x1, y1), (x2, y2), _NORMAL_COLOR, 4)
    return rendered


def render_annotated_video(
    source_path: Path,
    output_path: Path,
    frame_tracks: List[List[Track]],
    events,
    display_seconds: float = 1.5,
    labels: Optional[OverlayLabels] = None,
) -> None:
    """Render annotated video with alert highlighting for pickups."""
    confirmed = [event for event in events if event.pickup_confirmed]
    observed = [event for event in events if not event.pickup_confirmed]
    if not source_path.exists():
        return
    cap = cv2.VideoCapture(str(source_path))
    fps, width, height = get_video_info(cap)
    writer = create_video_writer(str(output_path), fps, width, height)
    frame_index = 0
    try:
        while cap.isOpened() and frame_index < len(frame_tracks):
            ok, frame = cap.read()
            if not ok:
                break
            t = frame_index / fps
            pickup_ids = {
                ev.track_id for ev in confirmed
                if ev.timestamp <= t <= ev.timestamp + display_seconds
            }
            observe_ids = {
                ev.track_id for ev in observed
                if ev.timestamp <= t <= ev.timestamp + display_seconds
            } - pickup_ids
            for track in frame_tracks[frame_index]:
                x1, y1, x2, y2 = track.bbox
                if track.track_id in pickup_ids:
                    _draw_alert_highlight(frame, x1, y1, x2, y2, "SUSPICIOUS", frame_index)
                elif track.track_id in observe_ids:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), _OBSERVE_COLOR, 3)
                else:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), _NORMAL_COLOR, 4)
            writer.write(frame)
            frame_index += 1
    finally:
        cap.release()
        writer.release()


def run_visual_pipeline(
    video_path: str,
    output_dir: str,
    zones: Optional[List[Zone]] = None,
    device: Optional[str] = None,
    yolo_weights: str = _DEFAULT_YOLO_WEIGHTS,
    tracker_config: str = "botsort.yaml",
    confidence: float = 0.6,
    semantic_interval_seconds: float = 1.0,
    evidence_window_seconds: float = 2.0,
    evidence_frames: int = 4,
    crop_pad: int = 120,
    interaction_trigger: bool = True,
    motion_threshold: float = 0.035,
    post_trigger_seconds: float = 0.5,
    vlm_max_image_size: int = 448,
    vlm_max_tokens: int = 96,
    vlm_backend: str = "minicpm-v",
    llama_model_path: Optional[str] = None,
    llama_mmproj_path: Optional[str] = None,
    llama_repo_id: str = "openbmb/MiniCPM-V-4.6-gguf",
    llama_filename: str = "MiniCPM-V-4_6-F16.gguf",
    llama_mmproj_filename: str = "mmproj-model-f16.gguf",
    llama_threads: Optional[int] = None,
    llama_context: int = 8192,
    llama_gpu_layers: int = -1,
    max_frames: Optional[int] = None,
    write_annotated_video: bool = True,
    progress: Optional[Callable[..., None]] = None,
    on_event: Optional[Callable] = None,
    preloaded_tracker=None,
    preloaded_vlm=None,
    locale: str = "en",
    stop_event=None,
) -> VisualPipelineResult:
    """Run the complete visual processing track on one video."""
    source = Path(video_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(source)
    out_dir = Path(output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(source))
    if not cap.isOpened():
        raise ValueError(f"could not open video: {source}")
    fps, width, height = get_video_info(cap)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if max_frames is not None:
        total_frames = min(total_frames, max_frames)

    resolved_zones = zones or [
        _zone_from_filename(source.stem, width, height)
        or full_frame_zone(width, height)
    ]
    resolved_device = device or get_device()
    tracker = preloaded_tracker or PersonTracker(
        weights=yolo_weights,
        tracker=tracker_config,
        conf=confidence,
        device=resolved_device,
    )
    reset_tracker = getattr(tracker, "reset", None)
    if callable(reset_tracker):
        reset_tracker()
    if preloaded_vlm is not None:
        vlm = preloaded_vlm
    elif vlm_backend == "llama-cpp-python":
        vlm = LlamaCppMiniCPMVLM(
            model_path=llama_model_path,
            mmproj_path=llama_mmproj_path,
            repo_id=llama_repo_id,
            filename=llama_filename,
            mmproj_filename=llama_mmproj_filename,
            n_ctx=llama_context,
            n_threads=llama_threads,
            n_gpu_layers=llama_gpu_layers,
            max_image_size=vlm_max_image_size,
            max_new_tokens=vlm_max_tokens,
        )
    else:
        vlm_dtype = "float16" if resolved_device in {"mps", "cuda"} else "auto"
        vlm = MiniCPMVLM(
            device=resolved_device,
            dtype=vlm_dtype,
            max_image_size=vlm_max_image_size,
            max_new_tokens=vlm_max_tokens,
        )
    structurer = EventStructurer(
        resolved_zones,
        vlm=vlm,
        crop_pad=crop_pad,
        semantic_interval_s=semantic_interval_seconds,
        evidence_window_s=evidence_window_seconds,
        evidence_frames=evidence_frames,
        interaction_trigger=interaction_trigger,
        motion_threshold=motion_threshold,
        post_trigger_s=post_trigger_seconds,
    )

    # Mutable cell so the VLM-start hook always reads the current frame state.
    _frame_info: List[int] = [
        0,
        total_frames or 0,
        0,
    ]  # [frame_index, total, track_count]
    if progress:
        try:
            progress_parameters = inspect.signature(progress).parameters.values()
            progress_accepts_frame = (
                any(
                    parameter.kind == parameter.VAR_POSITIONAL
                    for parameter in progress_parameters
                )
                or len(progress_parameters) >= 5
            )
        except (TypeError, ValueError):
            progress_accepts_frame = True

        def _report_progress(
            done: int,
            total: int,
            track_count: int,
            vlm_fired: bool,
            annotated_frame=None,
        ) -> None:
            if progress_accepts_frame:
                progress(done, total, track_count, vlm_fired, annotated_frame)
            else:
                progress(done, total, track_count, vlm_fired)

        def _on_vlm_start() -> None:
            _report_progress(_frame_info[0], _frame_info[1], _frame_info[2], True)

        structurer.on_vlm_start = _on_vlm_start
    else:
        _report_progress = None

    overlay_labels = OverlayLabels(locale)
    annotated_path = out_dir / f"{source.stem}_annotated.mp4"
    writer = None
    if write_annotated_video:
        writer = create_video_writer(str(annotated_path), fps, width, height)

    seen_tracks = set()
    frame_tracks: List[List[Track]] = []
    frame_index = 0
    try:
        while cap.isOpened() and (max_frames is None or frame_index < max_frames):
            if stop_event is not None and stop_event.is_set():
                break
            ok, frame = cap.read()
            if not ok:
                break
            t = frame_index / fps
            tracks = tracker.track(frame)
            frame_tracks.append(list(tracks))
            seen_tracks.update(track.track_id for track in tracks)
            frame_index += 1
            _frame_info[:] = [frame_index, total_frames or 0, len(tracks)]
            fired = structurer.update(tracks, t, latest_frame=frame)
            if on_event and fired:
                on_event([e.as_dict() for e in fired])
            annotated_frame = (
                draw_tracks(
                    frame,
                    tracks,
                    resolved_zones,
                    structurer.display_statuses(),
                    labels=overlay_labels,
                )
                if (writer is not None or progress)
                else None
            )
            if progress:
                _report_progress(
                    frame_index, total_frames, len(tracks), False, annotated_frame
                )
            if writer is not None:
                writer.write(annotated_frame)
    finally:
        cap.release()
        if writer is not None:
            writer.release()

    structurer.finalize_pending_pickups()
    if writer is not None:
        render_annotated_video(
            source, annotated_path, frame_tracks, structurer.events, labels=overlay_labels
        )

    events_path = out_dir / "events.json"
    events = [event.as_dict() for event in structurer.events]
    with events_path.open("w", encoding="utf-8") as handle:
        json.dump(events, handle, indent=2)

    # Do not leave a stale aggregate from older pipeline runs.
    (out_dir / "statuses.json").unlink(missing_ok=True)

    config_path = out_dir / "run_config.json"
    config = {
        "video_path": str(source),
        "device": resolved_device,
        "yolo_weights": yolo_weights,
        "tracker": tracker_config,
        "confidence": confidence,
        "vlm_backend": vlm.backend,
        "llama_model_path": llama_model_path,
        "llama_mmproj_path": llama_mmproj_path,
        "llama_repo_id": llama_repo_id if vlm_backend == "llama-cpp-python" else None,
        "llama_filename": llama_filename if vlm_backend == "llama-cpp-python" else None,
        "llama_mmproj_filename": (
            llama_mmproj_filename if vlm_backend == "llama-cpp-python" else None
        ),
        "llama_threads": llama_threads,
        "llama_context": llama_context if vlm_backend == "llama-cpp-python" else None,
        "llama_gpu_layers": (
            llama_gpu_layers if vlm_backend == "llama-cpp-python" else None
        ),
        "semantic_interval_seconds": semantic_interval_seconds,
        "evidence_window_seconds": evidence_window_seconds,
        "evidence_frames": evidence_frames,
        "crop_pad": crop_pad,
        "interaction_trigger": interaction_trigger,
        "motion_threshold": motion_threshold,
        "post_trigger_seconds": post_trigger_seconds,
        "vlm_max_image_size": vlm_max_image_size,
        "vlm_max_tokens": vlm_max_tokens,
        "zones": [
            {"name": z.name, "bbox": list(z.bbox), "kind": z.kind}
            for z in resolved_zones
        ],
    }
    with config_path.open("w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)

    return VisualPipelineResult(
        video_path=str(source),
        events_path=str(events_path),
        annotated_video_path=str(annotated_path) if writer is not None else None,
        frames_processed=frame_index,
        unique_tracks=len(seen_tracks),
        events=events,
    )
