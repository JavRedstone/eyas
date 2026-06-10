"""Command-line entry point for the complete Eyas visual processing track."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.paths import models_dir  # noqa: E402

_DEFAULT_WEIGHTS = str(models_dir() / "yolo11n.pt")

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
        raise argparse.ArgumentTypeError("zone must use NAME:KIND:X1,Y1,X2,Y2") from exc
    return Zone(name=name, kind=kind, bbox=bbox)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", help="Input MP4/MOV path")
    parser.add_argument("--output-dir", default="output/visual")
    parser.add_argument("--device", choices=["cpu", "mps", "cuda"], default=None)
    parser.add_argument("--weights", default=_DEFAULT_WEIGHTS)
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
        default=1.5,
        help="Minimum seconds between MiniCPM-V reviews per track. Default: 1.",
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
        default=4,
        help="Maximum ordered snapshots supplied per observation. Default: 4.",
    )
    parser.add_argument(
        "--crop-pad",
        type=int,
        default=50,
        help="Pixels of shelf/hand context around the combined person track. Default: 30.",
    )
    parser.add_argument(
        "--continuous-vlm",
        action="store_true",
        help="Run VLM periodically instead of only after interaction-motion triggers.",
    )
    parser.add_argument(
        "--motion-threshold",
        type=float,
        default=0.025,
        help="Changed-pixel ratio that triggers VLM review. Lower is more sensitive.",
    )
    parser.add_argument(
        "--post-trigger",
        type=float,
        default=0.5,
        help="Seconds to wait after interaction motion before VLM review. Default: 0.5.",
    )
    parser.add_argument(
        "--vlm-max-image-size",
        type=int,
        default=448,
        help="Maximum VLM crop dimension in pixels. Lower is faster. Default: 448.",
    )
    parser.add_argument(
        "--vlm-max-tokens",
        type=int,
        default=96,
        help=(
            "Maximum tokens generated per VLM observation. Use at least 96 for "
            "the full JSON response. Default: 96."
        ),
    )
    parser.add_argument(
        "--vlm-backend",
        choices=["transformers", "llama-cpp-python"],
        default="transformers",
        help="MiniCPM-V inference backend. Default: transformers.",
    )
    parser.add_argument(
        "--llama-model-path",
        help="Optional local MiniCPM-V 4.6 GGUF path. Otherwise download from Hugging Face.",
    )
    parser.add_argument(
        "--llama-mmproj-path",
        help="Optional local MiniCPM-V 4.6 multimodal projector GGUF path.",
    )
    parser.add_argument(
        "--llama-repo-id",
        default="openbmb/MiniCPM-V-4.6-gguf",
        help="Hugging Face GGUF repository used when --llama-model-path is omitted.",
    )
    parser.add_argument(
        "--llama-filename",
        default="MiniCPM-V-4_6-F16.gguf",
        help="GGUF filename selected from --llama-repo-id. Default: F16.",
    )
    parser.add_argument(
        "--llama-mmproj-filename",
        default="mmproj-model-f16.gguf",
        help="Vision projector selected from --llama-repo-id. Default: F16.",
    )
    parser.add_argument("--llama-threads", type=int)
    parser.add_argument("--llama-context", type=int, default=8192)
    parser.add_argument(
        "--llama-gpu-layers",
        type=int,
        default=-1,
        help="Layers offloaded by llama.cpp; -1 requests all layers. Default: -1.",
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

    def show_progress(
        done: int,
        total: int,
        track_count: int,
        vlm_fired: bool,
    ) -> None:
        if not vlm_fired and done != 1 and done % 30 != 0 and done != total:
            return
        suffix = f"/{total}" if total > 0 else ""
        stage = "VLM review" if vlm_fired else "processed"
        print(f"{stage}: frame {done}{suffix}, tracks: {track_count}", flush=True)

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
        interaction_trigger=not args.continuous_vlm,
        motion_threshold=args.motion_threshold,
        post_trigger_seconds=args.post_trigger,
        vlm_max_image_size=args.vlm_max_image_size,
        vlm_max_tokens=args.vlm_max_tokens,
        vlm_backend=args.vlm_backend,
        llama_model_path=args.llama_model_path,
        llama_mmproj_path=args.llama_mmproj_path,
        llama_repo_id=args.llama_repo_id,
        llama_filename=args.llama_filename,
        llama_mmproj_filename=args.llama_mmproj_filename,
        llama_threads=args.llama_threads,
        llama_context=args.llama_context,
        llama_gpu_layers=args.llama_gpu_layers,
        max_frames=args.max_frames,
        write_annotated_video=not args.no_annotated_video,
        progress=show_progress,
    )
    print(result.summary())
    print(f"events: {result.events_path}")
    if result.annotated_video_path:
        print(f"annotated video: {result.annotated_video_path}")


if __name__ == "__main__":
    start_time = time.time()
    main()

    print(f"Total Time for Inference: {time.time() - start_time:.2f}s")
