"""Fuse YOLO tracks with periodic MiniCPM-V appearance/activity observations."""

from __future__ import annotations

import json
from collections import deque
from dataclasses import asdict, dataclass, field
from typing import Deque, Dict, List, Optional, Tuple

import numpy as np

from object_detection.detector import Track
from video_processing.process import MiniCPMVLM, PersonObservation


@dataclass
class Zone:
    name: str
    bbox: Tuple[int, int, int, int]
    kind: str = "review"

    def contains_point(self, x: float, y: float) -> bool:
        x1, y1, x2, y2 = self.bbox
        return x1 <= x <= x2 and y1 <= y <= y2


@dataclass
class PersonStatus:
    track_id: int
    description: str = ""
    current_activity: str = ""
    current_held_objects: List[Dict] = field(default_factory=list)
    confirmed_pickups: List[Dict] = field(default_factory=list)
    summary: str = ""
    current_zone: str = ""
    first_seen: float = 0.0
    last_seen: float = 0.0
    observations: int = 0
    backend: str = ""
    raw_observation: str = ""
    bbox: List[int] = field(default_factory=list)

    def as_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ObservationEvent:
    track_id: int
    timestamp: float
    description: str
    activity: str
    held_objects: List[Dict]
    pickup_confirmed: bool
    picked_up_items: List[Dict]
    summary: str
    zone: str
    backend: str
    raw_observation: str
    bbox: List[int]
    confidence: float

    def as_dict(self) -> Dict:
        return asdict(self)


@dataclass
class TrackSnapshot:
    timestamp: float
    frame: np.ndarray
    bbox: Tuple[int, int, int, int]


class EventStructurer:
    """Track people continuously and periodically ask MiniCPM-V what each is doing."""

    def __init__(
        self,
        zones: List[Zone],
        vlm: Optional[MiniCPMVLM] = None,
        crop_pad: int = 120,
        semantic_interval_s: float = 1.0,
        evidence_window_s: float = 2.0,
        evidence_frames: int = 5,
        minimum_pickup_area_ratio: float = 0.03,
    ) -> None:
        self.zones = zones
        self.vlm = vlm if vlm is not None else MiniCPMVLM()
        self.crop_pad = crop_pad
        self.semantic_interval_s = max(0.0, semantic_interval_s)
        self.evidence_window_s = max(0.1, evidence_window_s)
        self.evidence_frames = max(2, evidence_frames)
        self.minimum_pickup_area_ratio = max(0.0, minimum_pickup_area_ratio)
        self.events: List[ObservationEvent] = []
        self.statuses: Dict[int, PersonStatus] = {}
        self._last_semantic: Dict[int, float] = {}
        self._last_interaction: Dict[int, float] = {}
        self._track_history: Dict[int, Deque[TrackSnapshot]] = {}

    def _zone_for(self, track: Track) -> Optional[Zone]:
        x1, _, x2, y2 = track.bbox
        foot_x, foot_y = (x1 + x2) / 2.0, float(y2)
        return next(
            (zone for zone in self.zones if zone.contains_point(foot_x, foot_y)),
            None,
        )

    def _merge_items(self, existing: List[Dict], observed: List[Dict]) -> List[Dict]:
        counts = {item["name"]: int(item["count"]) for item in existing}
        for item in observed:
            counts[item["name"]] = max(counts.get(item["name"], 0), int(item["count"]))
        return [{"name": name, "count": count} for name, count in counts.items()]

    def _remember(self, track: Track, t: float, frame: np.ndarray) -> None:
        history = self._track_history.setdefault(track.track_id, deque())
        minimum_gap = self.evidence_window_s / max(1, self.evidence_frames - 1)
        if not history or t - history[-1].timestamp >= minimum_gap:
            history.append(TrackSnapshot(t, frame.copy(), track.bbox))
        cutoff = t - self.evidence_window_s
        while history and history[0].timestamp < cutoff:
            history.popleft()

    def _evidence_crops(self, track_id: int) -> List[np.ndarray]:
        """Crop ordered snapshots to one shared region so item motion is visible."""
        snapshots = list(self._track_history.get(track_id, ()))
        if not snapshots:
            return []
        height, width = snapshots[-1].frame.shape[:2]
        x1 = max(0, min(snapshot.bbox[0] for snapshot in snapshots) - self.crop_pad)
        y1 = max(0, min(snapshot.bbox[1] for snapshot in snapshots) - self.crop_pad)
        x2 = min(width, max(snapshot.bbox[2] for snapshot in snapshots) + self.crop_pad)
        y2 = min(height, max(snapshot.bbox[3] for snapshot in snapshots) + self.crop_pad)
        return [snapshot.frame[y1:y2, x1:x2] for snapshot in snapshots]

    def update(
        self,
        tracks: List[Track],
        t: float,
        latest_frame: Optional[np.ndarray] = None,
    ) -> List[ObservationEvent]:
        fired: List[ObservationEvent] = []
        if latest_frame is None:
            return fired

        for track in tracks:
            zone = self._zone_for(track)
            status = self.statuses.get(track.track_id)
            if status is None:
                status = PersonStatus(track_id=track.track_id, first_seen=round(t, 2))
                self.statuses[track.track_id] = status
            status.last_seen = round(t, 2)
            status.current_zone = zone.name if zone else ""
            status.bbox = list(track.bbox)
            self._remember(track, t, latest_frame)

            if t - self._last_semantic.get(track.track_id, -1e9) < self.semantic_interval_s:
                continue
            frames = self._evidence_crops(track.track_id)
            if not frames or frames[-1].size == 0:
                continue
            observation: PersonObservation = self.vlm.observe_person(
                frames, track_id=track.track_id
            )
            self._last_semantic[track.track_id] = t

            activity_text = f"{observation.description} {observation.activity}".lower()
            interaction_visible = any(
                phrase in activity_text
                for phrase in ("reaching", "interacting", "handling", "pick up", "picking")
            )
            previous_held = status.current_held_objects
            frame_height, frame_width = latest_frame.shape[:2]
            x1, y1, x2, y2 = track.bbox
            track_area_ratio = (
                max(0, x2 - x1) * max(0, y2 - y1) / (frame_width * frame_height)
            )
            recent_interaction = (
                t - self._last_interaction.get(track.track_id, -1e9)
                <= self.evidence_window_s * 2.5
            )
            if (
                observation.held_objects
                and not previous_held
                and recent_interaction
                and track_area_ratio >= self.minimum_pickup_area_ratio
                and not observation.pickup_confirmed
            ):
                observation.pickup_confirmed = True
                observation.picked_up_items = list(observation.held_objects)
            if interaction_visible:
                self._last_interaction[track.track_id] = t

            status.description = observation.description or status.description
            status.current_activity = observation.activity
            status.current_held_objects = observation.held_objects
            if observation.pickup_confirmed:
                status.confirmed_pickups = self._merge_items(
                    status.confirmed_pickups, observation.picked_up_items
                )
            status.summary = " ".join(
                part for part in [status.description, status.current_activity] if part
            )
            status.observations += 1
            status.backend = observation.backend
            status.raw_observation = observation.raw

            event = ObservationEvent(
                track_id=track.track_id,
                timestamp=round(t, 2),
                description=observation.description,
                activity=observation.activity,
                held_objects=observation.held_objects,
                pickup_confirmed=observation.pickup_confirmed,
                picked_up_items=observation.picked_up_items,
                summary=status.summary,
                zone=status.current_zone,
                backend=observation.backend,
                raw_observation=observation.raw,
                bbox=list(track.bbox),
                confidence=round(track.confidence, 3),
            )
            self.events.append(event)
            fired.append(event)
        return fired

    def statuses_as_list(self) -> List[Dict]:
        return [status.as_dict() for status in self.statuses.values()]

    def to_json(self, path: Optional[str] = None) -> str:
        text = json.dumps([event.as_dict() for event in self.events], indent=2)
        if path:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(text)
        return text


def build_events(detections: List[Dict], annotations: List[Dict]) -> List[Dict]:
    """Legacy batch API retained for compatibility."""
    return []
