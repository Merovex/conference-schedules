#!/usr/bin/env python3
"""Convert a legacy sessions.json ({updated_at, sessions:[...]}) into data/cons/<slug>.yaml.

    python3 scripts/sessions_json_to_yaml.py sessions.json data/cons/author-nation-2026.yaml
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from yaml_out import write_sessions

src, dst = sys.argv[1], sys.argv[2]
d = json.loads(Path(src).read_text(encoding="utf-8"))
sessions = d["sessions"] if isinstance(d, dict) else d
for i, s in enumerate(sessions):
    s.setdefault("id", i)
write_sessions(Path(dst), sessions, updated_at=d.get("updated_at") if isinstance(d, dict) else None)
