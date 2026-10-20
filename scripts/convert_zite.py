#!/usr/bin/env python3
"""Refresh data/cons/<slug>.yaml from a Zite schedule app's getScheduleData export,
keeping the ids of sessions that already exist so bookmarks and Share links survive.

    curl -s -X POST https://workflows.zite.com/public/<flow-id>/api/getScheduleData \\
      -H 'Content-Type: application/json' -d '{"inputs":{},"mode":"live"}' \\
      -o scripts/<slug>.zite.json
    python3 scripts/convert_zite.py scripts/<slug>.zite.json data/cons/<slug>.yaml \\
      [--tz America/Los_Angeles] [--map OLD_ID=recXXXX ...]

Existing sessions are matched, in order, by: source_id (the Zite scheduleId,
stored on every row this script writes); title + date + start + room; title
alone when it is unique. --map pins an old id to a scheduleId by hand, for a
placeholder ("Sudowrite") that the organizer later gave a real title. Matched
sessions keep their id; unmatched old sessions are dropped (their id is
retired, never reused); new sessions are appended with fresh ids, in
chronological order.

Tags: track (SPLIT_TRACK breaks "Entertainment, Meetups & Networking" into
two), then format, then level, de-duplicated. A matched session whose title is
unchanged but whose speakers the source has since blanked keeps its old speakers.
"""
import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import sys
sys.path.insert(0, str(Path(__file__).parent))
from yaml_out import write_sessions

SPLIT_TRACK = {"Entertainment, Meetups & Networking": ["Entertainment", "Meetups & Networking"]}
FIX_TAG = {"Afinity Group": "Affinity Group", "Private - Invite only": "Invite Only"}


def ws(s):
    return re.sub(r"\s+", " ", s).strip() if s else s


def fmt_time(dt):
    h = dt.hour % 12 or 12
    return f"{h}:{dt.minute:02d} {'AM' if dt.hour < 12 else 'PM'}"


def speakers(n):
    names = [ws(p["name"]) for p in n.get("speakers") or []]
    if not names and n.get("speakerNames"):
        names = [ws(x) for x in n["speakerNames"].split(",") if x.strip()]
    out = []
    for name in names:
        half = name.split(" ")
        if len(half) % 2 == 0 and half[: len(half) // 2] == half[len(half) // 2:]:
            name = " ".join(half[: len(half) // 2])  # "Matt Landry Matt Landry"
        if name not in out:
            out.append(name)
    return out


def tags(n):
    track = ws(n.get("track") or "")
    raw = SPLIT_TRACK.get(track, [track]) + [n.get("format") or "", n.get("level") or ""]
    out = []
    for t in raw:
        t = FIX_TAG.get(ws(t), ws(t))
        if t and t not in out:
            out.append(t)
    return out


def row(n, tz):
    dt = datetime.fromisoformat(n["sessionDateTime"].replace("Z", "+00:00")).astimezone(tz)
    return {
        "source_id": n["scheduleId"],
        "title": ws(n["sessionTitle"]),
        "date": dt.strftime("%Y-%m-%d"),
        "day": dt.strftime("%A"),
        "start": fmt_time(dt),
        "duration_min": n.get("durationMin"),
        "speakers": speakers(n),
        "location": ws(n.get("room")),
        "tags": tags(n),
        "description": ws(n.get("description")) or None,
        "_dt": dt,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--tz", default="America/Los_Angeles")
    ap.add_argument("--map", action="append", default=[], help="OLD_ID=scheduleId")
    a = ap.parse_args()

    import yaml
    tz = ZoneInfo(a.tz)
    new = [row(n, tz) for n in json.loads(a.src.read_text(encoding="utf-8"))["sessions"]]
    prev = yaml.safe_load(a.out.read_text(encoding="utf-8")) if a.out.exists() else {}
    old = prev.get("sessions") or []
    pinned = {int(k): v for k, v in (m.split("=", 1) for m in a.map)}

    by_src = {n["source_id"]: n for n in new}
    taken, ids = set(), {}

    def claim(o, n):
        ids[n["source_id"]] = o["id"]
        taken.add(n["source_id"])

    passes = [
        lambda o, n: n["source_id"] == pinned.get(o["id"]) or n["source_id"] == o.get("source_id"),
        lambda o, n: n["title"].lower() == o["title"].lower()
        and (n["date"], n["start"], n["location"]) == (o["date"], o["start"], o["location"]),
        lambda o, n: n["title"].lower() == o["title"].lower(),
    ]
    for p, match in enumerate(passes):
        for o in old:
            if o["id"] in ids.values():
                continue
            hits = [n for n in new if n["source_id"] not in taken and match(o, n)]
            if len(hits) == 1 or (hits and p < 2):
                claim(o, hits[0])
    missing = [s for s in pinned.values() if s not in by_src]
    if missing:
        sys.exit(f"--map scheduleId not in export: {missing}")

    next_id = max([o["id"] for o in old] + [-1]) + 1
    for n in sorted(new, key=lambda n: (n["_dt"], n["title"])):
        if n["source_id"] not in ids:
            ids[n["source_id"]] = next_id
            next_id += 1

    sessions = sorted(new, key=lambda n: ids[n["source_id"]])
    by_id = {o["id"]: o for o in old}
    for n in sessions:
        n["id"] = ids[n["source_id"]]
        del n["_dt"]
        o = by_id.get(n["id"])
        if o and not n["speakers"] and o["speakers"] and o["title"].lower() == n["title"].lower():
            n["speakers"] = o["speakers"]

    dropped = [o for o in old if o["id"] not in ids.values()]
    for o in dropped:
        print(f"dropped id {o['id']}: {o['title']} ({o['date']} {o['start']})")

    extra = {k: prev[k] for k in ("conference", "filter") if k in prev}
    extra["venue_timezone"] = a.tz
    extra["source"] = f"Zite schedule app, getScheduleData export ({a.src.name})"
    write_sessions(a.out, sessions, extra=extra)


if __name__ == "__main__":
    main()
