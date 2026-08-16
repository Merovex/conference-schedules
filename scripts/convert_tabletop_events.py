#!/usr/bin/env python3
"""Convert a tabletop.events-derived events JSON into data/cons/<slug>.yaml.

    python3 scripts/convert_tabletop_events.py scripts/travellercon-usa-2026.events.json data/cons/travellercon-usa-2026.yaml

The output uses the schedule schema shared with the Author Nation site:
  title, date, day, start, duration_min, speakers, location, tags, description, id
plus `event_number` (the convention's own id) for reference.

Tags: the first tag is the event type (Panel / RPG / Miniatures); a second
"DGS" tag is added for "DGS Presents" events so they can be filtered together.
"""
import json
import re
import sys
from datetime import datetime, date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from yaml_out import write_sessions
SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2])

TYPE_TAG = {
    "Panels": "Panel",
    "RPG - (In-Person)": "RPG",
    "Miniatures - (In-Person ONLY)": "Miniatures",
}


def fmt_time(dt: datetime) -> str:
    h = dt.hour % 12 or 12
    return f"{h}:{dt.minute:02d} {'AM' if dt.hour < 12 else 'PM'}"


def main() -> None:
    src = json.loads(SRC.read_text(encoding="utf-8"))
    events = src["events"]

    rows = []
    for ev in events:
        start = datetime.fromisoformat(ev["start"])
        tags = [TYPE_TAG.get(ev["type"], ev["type"])]
        if re.match(r"^\s*DGS Presents", ev["title"]):
            tags.append("DGS")
        rows.append({
            "title": ev["title"].strip(),
            "date": start.date().isoformat(),
            "day": start.strftime("%A"),
            "start": fmt_time(start),
            "duration_min": int(ev["duration_minutes"]),
            "speakers": [],
            "location": ev.get("room") or None,
            "tags": tags,
            "description": (ev.get("summary") or "").strip() or None,
            "event_number": ev["event_number"],
            "_sort": start,
        })

    # chronological, then by title, so ids are stable and grouping is natural
    rows.sort(key=lambda r: (r["_sort"], r["title"]))
    for i, r in enumerate(rows):
        r["id"] = i

    for r in rows:
        r.pop("_sort")
    write_sessions(OUT, rows, extra={
        "conference": src["convention"],
        "venue_timezone": src["timezone"],
        "source": src["source"],
        "filter": src.get("filter"),
    })


if __name__ == "__main__":
    main()
