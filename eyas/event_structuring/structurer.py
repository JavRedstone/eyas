"""Fuse YOLO tracks with periodic MiniCPM-V appearance/activity observations."""

from __future__ import annotations

import json
import re
from collections import deque
from dataclasses import asdict, dataclass, field
from difflib import SequenceMatcher
from typing import Deque, Dict, List, Optional, Tuple

import numpy as np
import cv2

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
    source_track_ids: List[int] = field(default_factory=list)
    description: str = ""
    current_activity: str = ""
    current_held_objects: List[Dict] = field(default_factory=list)
    pickup_suspected: bool = False
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
    pickup_suspected: bool
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
        reid_max_gap_s: float = 15.0,
        reid_similarity_threshold: float = 0.40,
    ) -> None:
        self.zones = zones
        self.vlm = vlm if vlm is not None else MiniCPMVLM()
        self.crop_pad = crop_pad
        self.semantic_interval_s = max(0.0, semantic_interval_s)
        self.evidence_window_s = max(0.1, evidence_window_s)
        self.evidence_frames = max(2, evidence_frames)
        self.minimum_pickup_area_ratio = max(0.0, minimum_pickup_area_ratio)
        self.reid_max_gap_s = max(0.0, reid_max_gap_s)
        self.reid_similarity_threshold = min(1.0, max(0.0, reid_similarity_threshold))
        self.events: List[ObservationEvent] = []
        self.statuses: Dict[int, PersonStatus] = {}
        self._raw_to_person: Dict[int, int] = {}
        self._appearance_histograms: Dict[int, np.ndarray] = {}
        self._last_semantic: Dict[int, float] = {}
        self._pending_pickup_event: Dict[int, ObservationEvent] = {}
        self._track_history: Dict[int, Deque[TrackSnapshot]] = {}

    def _description_similarity(self, left: str, right: str) -> float:
        stopwords = {
            "a", "an", "and", "at", "in", "is", "near", "of", "on", "person",
            "retail", "standing", "store", "the", "with",
        }
        normalize = lambda text: {
            token for token in re.findall(r"[a-z0-9]+", text.lower())
            if token not in stopwords
        }
        left_tokens, right_tokens = normalize(left), normalize(right)
        if not left_tokens or not right_tokens:
            return 0.0
        overlap = len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
        sequence = SequenceMatcher(None, " ".join(sorted(left_tokens)), " ".join(sorted(right_tokens))).ratio()
        return 0.65 * overlap + 0.35 * sequence

    def _reidentify(
        self,
        raw_track_id: int,
        description: str,
        appearance: np.ndarray,
        t: float,
        active_person_ids: set,
    ) -> Optional[int]:
        if not description:
            return None
        best_id, best_score = None, self.reid_similarity_threshold
        for person_id, candidate in self.statuses.items():
            if person_id == raw_track_id or person_id in active_person_ids:
                continue
            gap = t - candidate.last_seen
            if gap < 0 or gap > self.reid_max_gap_s:
                continue
            description_score = self._description_similarity(description, candidate.description)
            candidate_appearance = self._appearance_histograms.get(person_id)
            appearance_score = (
                float(cv2.compareHist(appearance, candidate_appearance, cv2.HISTCMP_CORREL))
                if candidate_appearance is not None
                else 0.0
            )
            if appearance_score < 0.65:
                continue
            score = 0.55 * description_score + 0.45 * max(0.0, appearance_score)
            if score > best_score:
                best_id, best_score = person_id, score
        return best_id

    def _appearance_histogram(
        self, frame: np.ndarray, bbox: Tuple[int, int, int, int]
    ) -> np.ndarray:
        height, width = frame.shape[:2]
        x1, y1, x2, y2 = bbox
        x1, x2 = max(0, x1), min(width, x2)
        y1, y2 = max(0, y1), min(height, y2)
        person = frame[y1:y2, x1:x2]
        if person.size == 0:
            return np.zeros((32, 32), dtype=np.float32)
        hsv = cv2.cvtColor(person, cv2.COLOR_BGR2HSV)
        histogram = cv2.calcHist([hsv], [0, 1], None, [32, 32], [0, 180, 0, 256])
        return cv2.normalize(histogram, histogram).flatten()

    def _merge_status(self, target: PersonStatus, source: PersonStatus) -> None:
        target.source_track_ids = sorted(set(target.source_track_ids + source.source_track_ids))
        target.first_seen = min(target.first_seen, source.first_seen)
        target.confirmed_pickups = self._merge_items(
            target.confirmed_pickups, source.confirmed_pickups
        )

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

        active_person_ids = {
            self._raw_to_person.get(track.track_id, track.track_id) for track in tracks
        }
        for track in tracks:
            person_id = self._raw_to_person.get(track.track_id, track.track_id)
            zone = self._zone_for(track)
            status = self.statuses.get(person_id)
            if status is None:
                status = PersonStatus(
                    track_id=person_id,
                    source_track_ids=[track.track_id],
                    first_seen=round(t, 2),
                )
                self.statuses[person_id] = status
                self._raw_to_person[track.track_id] = person_id
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
                frames, track_id=person_id
            )
            self._last_semantic[track.track_id] = t
            appearance = self._appearance_histogram(latest_frame, track.bbox)

            if person_id == track.track_id and status.observations == 0:
                matched_id = self._reidentify(
                    track.track_id,
                    observation.description,
                    appearance,
                    t,
                    active_person_ids,
                )
                if matched_id is not None:
                    previous_status = status
                    status = self.statuses[matched_id]
                    self._merge_status(status, previous_status)
                    self.statuses.pop(person_id)
                    person_id = matched_id
                    self._raw_to_person[track.track_id] = person_id
                    active_person_ids.add(person_id)
                    status.last_seen = round(t, 2)
                    status.current_zone = zone.name if zone else ""
                    status.bbox = list(track.bbox)
            self._appearance_histograms[person_id] = appearance

            activity_text = f"{observation.description} {observation.activity}".lower()
            pickup_motion_visible = any(
                phrase in activity_text
                for phrase in ("reaching", "pick up", "picking")
            )
            ambiguous_pickup_motion = pickup_motion_visible and any(
                phrase in activity_text
                for phrase in ("possibly", "appears", "inspecting", "examining")
            )
            pickup_suspected = ambiguous_pickup_motion
            previous_held = status.current_held_objects
            frame_height, frame_width = latest_frame.shape[:2]
            x1, y1, x2, y2 = track.bbox
            track_area_ratio = (
                max(0, x2 - x1) * max(0, y2 - y1) / (frame_width * frame_height)
            )
            pending_event = self._pending_pickup_event.get(person_id)
            if (
                observation.held_objects
                and not previous_held
                and pending_event is not None
                and t - pending_event.timestamp <= 10.0
                and track_area_ratio >= self.minimum_pickup_area_ratio
                and not observation.pickup_confirmed
            ):
                pending_event.pickup_confirmed = True
                pending_event.picked_up_items = list(observation.held_objects)
                pending_event.confirmation_timestamp = round(t, 2)
                status.confirmed_pickups = self._merge_items(
                    status.confirmed_pickups, observation.held_objects
                )
                self._pending_pickup_event.pop(person_id, None)
                pickup_suspected = False

            status.description = observation.description or status.description
            status.current_activity = observation.activity
            status.current_held_objects = observation.held_objects
            status.pickup_suspected = pickup_suspected
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
                track_id=person_id,
                timestamp=round(t, 2),
                confirmation_timestamp=round(t, 2) if observation.pickup_confirmed else None,
                description=observation.description,
                activity=observation.activity,
                held_objects=observation.held_objects,
                pickup_suspected=pickup_suspected,
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
            if pickup_motion_visible and not observation.held_objects:
                self._pending_pickup_event[person_id] = event
        return fired

    def statuses_as_list(self) -> List[Dict]:
        return [status.as_dict() for status in self.statuses.values()]

    def display_statuses(self) -> Dict[int, PersonStatus]:
        """Map current raw YOLO IDs to their canonical person statuses."""
        return {
            raw_id: self.statuses[person_id]
            for raw_id, person_id in self._raw_to_person.items()
            if person_id in self.statuses
        }

    def to_json(self, path: Optional[str] = None) -> str:
        text = json.dumps([event.as_dict() for event in self.events], indent=2)
        if path:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(text)
        return text


def build_events(detections: List[Dict], annotations: List[Dict]) -> List[Dict]:
    """Legacy batch API retained for compatibility."""
    return []
