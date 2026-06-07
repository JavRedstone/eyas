"""Runnable visual pipeline: video -> YOLO tracks -> MiniCPM-V event log."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

import cv2

from event_structuring.structurer import EventStructurer, PersonStatus, Zone
from object_detection.detector import PersonTracker, Track
from video_processing.process import MiniCPMVLM


@dataclass
class VisualPipelineResult:
    video_path: str
    events_path: str
    statuses_path: str
    annotated_video_path: Optional[str]
    frames_processed: int
    unique_tracks: int
    events: List[dict]
    statuses: List[dict]
    def summary(self) -> str:
        return (
            f"Processed {self.frames_processed} frames, tracked "
            f"{self.unique_tracks} people, retained {len(self.statuses)} live statuses, "
            f"and generated {len(self.events)} MiniCPM-V observations."
        )


def auto_device() -> str:
    """Choose the best available PyTorch device for YOLO/MiniCPM-V."""
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
        if torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"


def full_frame_zone(width: int, height: int) -> Zone:
    """Development default that guarantees any tracked person can trigger."""
    return Zone(name="review_area", bbox=(0, 0, width, height), kind="shelf")


def draw_tracks(
    frame,
    tracks: List[Track],
    zones: List[Zone],
    statuses: Optional[Dict[int, PersonStatus]] = None,
):
    """Draw configured zones and current YOLO person tracks."""
    rendered = frame.copy()
    for zone in zones:
        x1, y1, x2, y2 = zone.bbox
        color = (0, 165, 255) if zone.kind == "shelf" else (255, 180, 0)
        cv2.rectangle(rendered, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            rendered,
            f"{zone.name} ({zone.kind})",
            (x1 + 4, max(18, y1 + 18)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
        )
    for track in tracks:
        x1, y1, x2, y2 = track.bbox
        cv2.rectangle(rendered, (x1, y1), (x2, y2), (0, 255, 0), 2)
        status = statuses.get(track.track_id) if statuses else None
        label = status.description if status and status.description else f"person #{track.track_id}"
        label = f"#{track.track_id} {label}"[:80]
        cv2.putText(
            rendered,
            label,
            (x1, max(18, y1 - 7)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (0, 255, 0),
            2,
        )
        if status and status.current_activity:
            activity_label = status.current_activity[:70]
            activity_y = min(rendered.shape[0] - 8, y2 + 22)
            if activity_y <= y2:
                activity_y = max(18, y2 - 8)
            cv2.putText(
                rendered,
                activity_label,
                (x1, activity_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.52,
                (255, 255, 0),
                2,
            )
        if status and status.current_held_objects:
            held_text = ", ".join(
                f"HOLDING: {item['count']} x {item['name']}"
                for item in status.current_held_objects
            )[:70]
            cv2.putText(
                rendered,
                held_text,
                (x1, min(rendered.shape[0] - 8, y2 + 42)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                (0, 255, 255),
                2,
            )
        if status and status.confirmed_pickups:
            item_text = ", ".join(
                f"PICKUP: {item['count']} x {item['name']}"
                for item in status.confirmed_pickups
            )[:70]
            cv2.putText(
                rendered,
                item_text,
                (x1, min(rendered.shape[0] - 8, y2 + 62)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                (0, 0, 255),
                2,
            )
    return rendered


def run_visual_pipeline(
    video_path: str,
    output_dir: str,
    zones: Optional[List[Zone]] = None,
    device: Optional[str] = None,
    yolo_weights: str = "yolo11n.pt",
    tracker_config: str = "botsort.yaml",
    confidence: float = 0.6,
    semantic_interval_seconds: float = 1.0,
    evidence_window_seconds: float = 2.0,
    evidence_frames: int = 5,
    crop_pad: int = 120,
    minimum_pickup_area_ratio: float = 0.03,
    max_frames: Optional[int] = None,
    write_annotated_video: bool = True,
    progress: Optional[Callable[[int, int], None]] = None,
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
    fps = cap.get(cv2.CAP_PROP_FPS) or 12.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if max_frames is not None:
        total_frames = min(total_frames, max_frames)

    resolved_zones = zones or [full_frame_zone(width, height)]
    resolved_device = device or auto_device()
    tracker = PersonTracker(
        weights=yolo_weights,
        tracker=tracker_config,
        conf=confidence,
        device=resolved_device,
    )
    vlm_dtype = "float16" if resolved_device in {"mps", "cuda"} else "auto"
    vlm = MiniCPMVLM(device=resolved_device, dtype=vlm_dtype)
    structurer = EventStructurer(
        resolved_zones,
        vlm=vlm,
        crop_pad=crop_pad,
        semantic_interval_s=semantic_interval_seconds,
        evidence_window_s=evidence_window_seconds,
        evidence_frames=evidence_frames,
        minimum_pickup_area_ratio=minimum_pickup_area_ratio,
    )

    annotated_path = out_dir / f"{source.stem}_annotated.mp4"
    writer = None
    if write_annotated_video:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(annotated_path), fourcc, fps, (width, height))

    seen_tracks = set()
    frame_index = 0
    try:
        while cap.isOpened() and (max_frames is None or frame_index < max_frames):
            ok, frame = cap.read()
            if not ok:
                break
            t = frame_index / fps
            tracks = tracker.track(frame)
            seen_tracks.update(track.track_id for track in tracks)
            structurer.update(tracks, t, latest_frame=frame)
            if writer is not None:
                writer.write(draw_tracks(frame, tracks, resolved_zones, structurer.statuses))
            frame_index += 1
            if progress and (frame_index == 1 or frame_index % 30 == 0):
                progress(frame_index, total_frames)
    finally:
        cap.release()
        if writer is not None:
            writer.release()

    events_path = out_dir / "events.json"
    events = [event.as_dict() for event in structurer.events]
    with events_path.open("w", encoding="utf-8") as handle:
        json.dump(events, handle, indent=2)

    statuses_path = out_dir / "statuses.json"
    statuses = structurer.statuses_as_list()
    with statuses_path.open("w", encoding="utf-8") as handle:
        json.dump(statuses, handle, indent=2)

    config_path = out_dir / "run_config.json"
    config = {
        "video_path": str(source),
        "device": resolved_device,
        "yolo_weights": yolo_weights,
        "tracker": tracker_config,
        "confidence": confidence,
        "vlm_backend": "minicpmv",
        "semantic_interval_seconds": semantic_interval_seconds,
        "evidence_window_seconds": evidence_window_seconds,
        "evidence_frames": evidence_frames,
        "crop_pad": crop_pad,
        "minimum_pickup_area_ratio": minimum_pickup_area_ratio,
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
        statuses_path=str(statuses_path),
        annotated_video_path=str(annotated_path) if writer is not None else None,
        frames_processed=frame_index,
        unique_tracks=len(seen_tracks),
        events=events,
        statuses=statuses,
    )
