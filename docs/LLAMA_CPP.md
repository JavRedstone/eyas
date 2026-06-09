# MiniCPM-V with llama-cpp-python on an edge CPU

Eyas can load MiniCPM-V directly inside the Python process through
`llama-cpp-python`. No HTTP server or NVIDIA GPU is required.

The default backend downloads the official Q4 GGUF and matching Q8 vision
projector from `ggml-org/MiniCPM-V-4.6-GGUF`.

## Install for CPU

For x86 edge devices, build with OpenBLAS:

```bash
CMAKE_ARGS="-DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS" \
  pip install llama-cpp-python
```

Or install the basic CPU wheel:

```bash
pip install llama-cpp-python \
  --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

## Run fully locally

```bash
cd eyas

../.venv/bin/python scripts/run_visual_pipeline.py input/test.mp4 \
  --vlm-backend llama-cpp-python \
  --llama-threads 8 \
  --semantic-interval 1 \
  --evidence-window 2 \
  --evidence-frames 3 \
  --output-dir output/llama-cpp-python
```

The first run downloads `MiniCPM-V-4.6-Q4_K_M.gguf` and
`mmproj-MiniCPM-V-4.6-Q8_0.gguf` into the Hugging Face cache. Later runs are
fully local.

For CPU speed, begin with `--evidence-frames 3` and increase
`--semantic-interval` to `2` if necessary.

Other supported backends:

- `--vlm-backend transformers`: load MiniCPM-V through Transformers.
- `--vlm-backend llama-cpp`: connect to a separately running HTTP server.
