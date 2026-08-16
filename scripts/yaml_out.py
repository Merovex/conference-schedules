"""Shared emitter: writes the schedule YAML in the canonical field order, with
dates/times quoted so Hugo keeps them as strings."""
import json
from datetime import date
from pathlib import Path

FIELDS = ["id", "event_number", "title", "date", "day", "start", "duration_min",
          "speakers", "location", "tags", "description"]

def yq(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(yq(x) for x in v) + "]"
    return json.dumps(str(v), ensure_ascii=False)

def write_sessions(path: Path, sessions, updated_at=None, extra=None):
    lines = [f"updated_at: {yq(updated_at or date.today().isoformat())}"]
    for k, v in (extra or {}).items():
        lines.append(f"{k}: {yq(v)}")
    lines += [f"session_count: {len(sessions)}", "sessions:"]
    for s in sessions:
        first = True
        for f in FIELDS:
            if f not in s:
                continue
            v = s[f]
            if f == "day" and v:
                lines.append(f"    day: {v}")
                continue
            lines.append(("  - " if first else "    ") + f"{f}: {yq(v)}")
            first = False
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"wrote {path}: {len(sessions)} sessions")
