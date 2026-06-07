"""Convert detection streams and clip annotations into structured events."""

from typing import List, Dict


def build_events(detections: List[Dict], annotations: List[Dict]) -> List[Dict]:
    """Merge detections and annotations into a time-ordered event log.
    Each event should include: type, start_time, end_time, zone, metadata
    """
    # TODO: implement zoning, temporal grouping, and event heuristics
    return []
