# tests/e2e

Full end-to-end pipeline test — every real component, no stubs.

## Flow

```
samples/sample.mp4
  → PersonTracker (YOLO)
  → MiniCPMVLM   (real transformers model)
  → EventStructurer
  → Reasoner     (GGUF LLM)
  → samples/events.json  +  structured summary
```

## Skip conditions

Each test function is automatically skipped when its prerequisite is missing:

| Mark | Skipped when |
|---|---|
| `@requires_vlm` | `transformers` not installed |
| `@requires_reasoner` | GGUF model file not found |

## Run

```bash
# With all models present
pytest tests/e2e/ -v -s

# Override GGUF path
EYAS_MODEL_PATH=models/mymodel.gguf pytest tests/e2e/ -v -s

# As a standalone script (prints pass/fail to stdout)
python tests/e2e/test_pipeline_e2e.py
```
