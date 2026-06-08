# storage

Clip index — store, list, and delete uploaded or recorded footage.

## Key exports

| Symbol | Description |
|---|---|
| `store(path, source)` | Copy a clip into the managed `clips/` dir; append an entry to the JSON index |
| `list_clips()` | Return all index entries, newest first |
| `choices()` | Return human-readable label strings suitable for a Gradio dropdown |
| `path_from_choice(label)` | Resolve a `choices()` label back to a file path |
| `delete(filename)` | Remove a clip file and its index entry |

## Storage layout

```
clips/
  <uuid>_<original_filename>.mp4
clip_index.json   # [{filename, path, timestamp, source, size_mb}, …]
```

## Usage

```python
from storage import manager as storage

entry = storage.store("uploads/footage.mp4", source="upload")
for clip in storage.list_clips():
    print(clip["filename"], clip["size_mb"], "MB")
storage.delete(entry["filename"])
```
