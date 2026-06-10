"""Clip storage — copies inbound files to data/clips/ and maintains a JSON index."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

_DATA  = Path(__file__).parent.parent / "data"
_CLIPS = _DATA / "clips"
_INDEX = _DATA / "clip_index.json"


def _ensure() -> None:
    _CLIPS.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

def store(src_path: str, source: str = "upload") -> Dict:
    """Copy *src_path* into the clip store.  Returns the index entry."""
    _ensure()
    src  = Path(src_path)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"{ts}_{src.name}"
    dest = _CLIPS / name
    shutil.copy2(src, dest)
    entry: Dict = {
        "filename": name,
        "path":     str(dest),
        "timestamp": ts,
        "source":   source,
        "size_mb":  round(dest.stat().st_size / 1_000_000, 2),
    }
    _append(entry)
    return entry


def delete(filename: str) -> bool:
    try:
        (_CLIPS / filename).unlink(missing_ok=True)
        remaining = [c for c in _read_index() if c["filename"] != filename]
        _INDEX.write_text(json.dumps(remaining, indent=2))
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def list_clips() -> List[Dict]:
    """Newest-first list of stored clip records."""
    return _read_index()[::-1]


def choices(locale: str = "en") -> List[str]:
    """Dropdown-ready labels: 'YYYYMMDD_HHMMSS — name (X MB) [source]'."""
    from ui.locale import Strings

    s = Strings(locale)
    out = []
    for c in list_clips():
        ts = c["timestamp"]
        src = c.get("source", "upload")
        mb = c.get("size_mb", "?")
        src_label = s.storage_source_label(src)
        out.append(s.t(
            "storage.choice_format",
            ts=ts,
            filename=c["filename"],
            size_mb=mb,
            source=src_label,
        ))
    return out


def path_from_choice(choice: str) -> Optional[str]:
    """Resolve a choices() label back to an absolute file path."""
    # label format: 'timestamp — filename  (x MB)  [source]'
    try:
        filename = choice.split(" — ", 1)[1].split("  ")[0].strip()
        p = _CLIPS / filename
        return str(p) if p.exists() else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

def _read_index() -> List[Dict]:
    try:
        return json.loads(_INDEX.read_text())
    except Exception:
        return []


def _append(entry: Dict) -> None:
    existing = _read_index()
    existing.append(entry)
    _INDEX.write_text(json.dumps(existing, indent=2))
