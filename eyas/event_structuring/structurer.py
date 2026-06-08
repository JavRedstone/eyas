"""Fuse YOLO tracks with periodic MiniCPM-V appearance/activity observations."""

from __future__ import annotations

import json
import re
from collections import deque
from dataclasses import asdict, dataclass, field
from typing import Deque, Dict, List, Optional, Tuple

import numpy as np
import cv2

from object_detection.detector import Track
from video_processing.process import MiniCPMVLM, PersonObservation

PICKUP_ACTIVITY = re.compile(
    r"\b(?:"
    r"pick(?:s|ing|ed)?(?:\s+\w+){0,3}\s+up|"
    r"tak(?:ing|es?)|"
    r"select(?:ing|ed)?|"
    r"remov(?:ing|ed)|"
    r"(?:moves?|moving)\s+(?:his|her|their|the)?\s*hand\b.+\bthen\s+holds?"
    r")\b",
    re.IGNORECASE,
)
PICKUP_NEGATION = re.compile(
    r"\b(?:no|not|never|without|cannot|can't|doesn't|does\s+not|"
    r"didn't|did\s+not|isn't|is\s+not|aren't|are\s+not)\b",
    re.IGNORECASE,
)


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
    confirmation_timestamp: Optional[float]
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
        interaction_trigger: bool = False,
        motion_threshold: float = 0.035,
        post_trigger_s: float = 0.5,
    ) -> None:
        self.zones = zones
        self.vlm = vlm if vlm is not None else MiniCPMVLM()
        self.crop_pad = crop_pad
        self.semantic_interval_s = max(0.0, semantic_interval_s)
        self.evidence_window_s = max(0.1, evidence_window_s)
        self.evidence_frames = max(3, evidence_frames)
        self.interaction_trigger = interaction_trigger
        self.motion_threshold = max(0.0, motion_threshold)
        self.post_trigger_s = max(0.0, post_trigger_s)
        self.events: List[ObservationEvent] = []
        self.statuses: Dict[int, PersonStatus] = {}
        self._last_semantic: Dict[int, float] = {}
        self._pending_interactions: Dict[int, float] = {}
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

    def _motion_score(self, track_id: int) -> float:
        """Return the changed-pixel ratio between the latest two evidence crops."""
        crops = self._evidence_crops(track_id)
        if len(crops) < 2 or crops[-2].size == 0 or crops[-1].size == 0:
            return 0.0
        previous = cv2.resize(crops[-2], (160, 160), interpolation=cv2.INTER_AREA)
        current = cv2.resize(crops[-1], (160, 160), interpolation=cv2.INTER_AREA)
        previous_gray = cv2.GaussianBlur(cv2.cvtColor(previous, cv2.COLOR_BGR2GRAY), (5, 5), 0)
        current_gray = cv2.GaussianBlur(cv2.cvtColor(current, cv2.COLOR_BGR2GRAY), (5, 5), 0)
        difference = cv2.absdiff(previous_gray, current_gray)
        return float(np.count_nonzero(difference > 18) / difference.size)

    def _should_observe(self, track_id: int, t: float) -> bool:
        if not self.interaction_trigger:
            return t - self._last_semantic.get(track_id, -1e9) >= self.semantic_interval_s

        pending_at = self._pending_interactions.get(track_id)
        if pending_at is not None:
            if t - pending_at >= self.post_trigger_s:
                self._pending_interactions.pop(track_id, None)
                return True
            return False

        cooldown_ready = (
            t - self._last_semantic.get(track_id, -1e9) >= self.semantic_interval_s
        )
        if cooldown_ready and self._motion_score(track_id) >= self.motion_threshold:
            if self.post_trigger_s == 0:
                return True
            self._pending_interactions[track_id] = t
        return False

    def _activity_indicates_pickup(self, activity: str) -> bool:
        """Promote explicit pickup wording unless its surrounding clause negates it."""
        for match in PICKUP_ACTIVITY.finditer(activity):
            clause_start = max(
                activity.rfind(".", 0, match.start()),
                activity.rfind(";", 0, match.start()),
                activity.rfind("\n", 0, match.start()),
            ) + 1
            clause_end_candidates = [
                position for position in (
                    activity.find(".", match.end()),
                    activity.find(";", match.end()),
                    activity.find("\n", match.end()),
                )
                if position >= 0
            ]
            clause_end = min(clause_end_candidates, default=len(activity))
            clause = activity[clause_start:clause_end]
            if not PICKUP_NEGATION.search(clause):
                return True
        return False

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
            person_id = track.track_id
            zone = self._zone_for(track)
            status = self.statuses.get(person_id)
            if status is None:
                status = PersonStatus(
                    track_id=person_id,
                    first_seen=round(t, 2),
                )
                self.statuses[person_id] = status
            status.last_seen = round(t, 2)
            status.current_zone = zone.name if zone else ""
            status.bbox = list(track.bbox)
            self._remember(track, t, latest_frame)

            if not self._should_observe(track.track_id, t):
                continue
            frames = self._evidence_crops(track.track_id)
            if not frames or frames[-1].size == 0:
                continue
            observation: PersonObservation = self.vlm.observe_person(
                frames, track_id=person_id
            )
            self._last_semantic[track.track_id] = t

            activity_pickup = self._activity_indicates_pickup(observation.activity)
            pickup_confirmed = observation.pickup_confirmed or activity_pickup
            picked_up_items = list(observation.picked_up_items)
            if pickup_confirmed and not picked_up_items:
                picked_up_items = (
                    list(observation.held_objects)
                    if observation.held_objects
                    else [{"name": "retail item", "count": 1}]
                )

            status.description = observation.description or status.description
            status.current_activity = observation.activity
            status.current_held_objects = observation.held_objects
            if pickup_confirmed:
                status.confirmed_pickups = self._merge_items(
                    status.confirmed_pickups, picked_up_items
                )
            status.summary = " ".join(
                part for part in [status.description, status.current_activity] if part
            )
            status.observations += 1
            status.backend = observation.backend
            status.raw_observation = observation.raw

            event = ObservationEvent(
                track_id=person_id,
                timestamp=round(t, 2),
                confirmation_timestamp=round(t, 2) if pickup_confirmed else None,
                description=observation.description or status.description,
                activity=observation.activity,
                held_objects=observation.held_objects,
                pickup_confirmed=pickup_confirmed,
                picked_up_items=picked_up_items,
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

    def display_statuses(self) -> Dict[int, PersonStatus]:
        return self.statuses

    def to_json(self, path: Optional[str] = None) -> str:
        text = json.dumps([event.as_dict() for event in self.events], indent=2)
        if path:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(text)
        return text


def build_events(detections: List[Dict], annotations: List[Dict]) -> List[Dict]:
    """Legacy batch API retained for compatibility."""
    return []
