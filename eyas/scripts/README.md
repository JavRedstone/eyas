# scripts

CLI entry points and batch utilities. All commands run from the repo root.

## run_visual_pipeline.py

Run the full pipeline on a single video file.

```bash
python eyas/scripts/run_visual_pipeline.py eyas/input/sample.mp4 \
  --device cuda \
  --output-dir output/visual \
  --semantic-interval 1.0 \
  --language ko
```

Key flags: `--device`, `--weights`, `--confidence`, `--semantic-interval`, `--evidence-window`, `--zone NAME:KIND:X1,Y1,X2,Y2`, `--max-frames`, `--language {en,ko}`.

## split_clips.py

Chop a long recording into fixed-length segments for batch processing.

```bash
python eyas/scripts/split_clips.py footage.mp4 --clip-len 10
```

Writes `footage_clips/clip_0000.mp4`, `clip_0001.mp4`, … alongside the source file.

## sample.py

Quick sampling / demo helper. See the file header for usage.
