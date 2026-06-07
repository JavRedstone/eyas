"""Command-line entry point for the complete Eyas visual processing track."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_structuring.structurer import Zone  # noqa: E402
from visual_pipeline import run_visual_pipeline  # noqa: E402


def parse_zone(value: str) -> Zone:
    """Parse NAME:KIND:X1,Y1,X2,Y2."""
    try:
        name, kind, coords = value.split(":", 2)
        bbox = tuple(int(v) for v in coords.split(","))
        if len(bbox) != 4:
            raise ValueError
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "zone must use NAME:KIND:X1,Y1,X2,Y2"
        ) from exc
    return Zone(name=name, kind=kind, bbox=bbox)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", help="Input MP4/MOV path")
    parser.add_argument("--output-dir", default="output/visual")
    parser.add_argument("--device", choices=["cpu", "mps", "cuda"], default=None)
    parser.add_argument("--weights", default="yolo11n.pt")
    parser.add_argument("--tracker", default="botsort.yaml")
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.6,
        help="YOLO person detection confidence threshold. Default: 0.6.",
    )
    parser.add_argument(
        "--semantic-interval",
        type=float,
        default=1.0,
        help="Seconds between MiniCPM-V observations per track; 0 observes every frame.",
    )
    parser.add_argument(
        "--evidence-window",
        type=float,
        default=2.0,
        help="Seconds of causal track history supplied to MiniCPM-V. Default: 2.",
    )
    parser.add_argument(
        "--evidence-frames",
        type=int,
        default=5,
        help="Maximum ordered snapshots supplied per observation. Default: 5.",
    )
    parser.add_argument(
        "--crop-pad",
        type=int,
        default=120,
        help="Pixels of shelf/hand context around the combined person track. Default: 120.",
    )
    parser.add_argument(
        "--min-pickup-area-ratio",
        type=float,
        default=0.03,
        help="Minimum fraction of frame covered by a track for inferred pickups. Default: 0.03.",
    )
    parser.add_argument("--max-frames", type=int)
    parser.add_argument("--no-annotated-video", action="store_true")
    parser.add_argument(
        "--zone",
        action="append",
        type=parse_zone,
        help="Repeatable zone definition: NAME:KIND:X1,Y1,X2,Y2",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    def show_progress(done: int, total: int) -> None:
        suffix = f"/{total}" if total > 0 else ""
        print(f"processed frames: {done}{suffix}", flush=True)

    result = run_visual_pipeline(
        video_path=args.video,
        output_dir=args.output_dir,
        zones=args.zone,
        device=args.device,
        yolo_weights=args.weights,
        tracker_config=args.tracker,
        confidence=args.confidence,
        semantic_interval_seconds=args.semantic_interval,
        evidence_window_seconds=args.evidence_window,
        evidence_frames=args.evidence_frames,
        crop_pad=args.crop_pad,
        minimum_pickup_area_ratio=args.min_pickup_area_ratio,
        max_frames=args.max_frames,
        write_annotated_video=not args.no_annotated_video,
        progress=show_progress,
    )
    print(result.summary())
    print(f"events: {result.events_path}")
    print(f"statuses: {result.statuses_path}")
    if result.annotated_video_path:
        print(f"annotated video: {result.annotated_video_path}")


if __name__ == "__main__":
    main()
