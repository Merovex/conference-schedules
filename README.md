# Author Nation 2026 — Session Schedule

A single, self-contained web page that renders the conference schedule from a YAML
source. Pick the talks you want, share your picks via a compressed URL, and export
a nicely formatted PDF of your personal agenda.

## Files

| File | Purpose |
|------|---------|
| `index.html` | The whole app — Tailwind (CDN), Lucide icon sprite, dark/light, filters, bookmarks, PDF export. No build step, no framework. |
| `sessions.json` | The data the page loads at runtime (`fetch('sessions.json')`). An object `{ updated_at, count, sessions }`, generated from the YAML. |
| `_sessions.yml` | **The source of truth.** Human-edited list of sessions. |
| `parse_sessions.rb` | Converts `_sessions.yml` → `sessions.json` (tolerant of mixed formatting). |

The page fetches `sessions.json` **on the fly**, so editing the YAML never touches
`index.html` — you only regenerate the JSON.

## Usage

```bash
# 1. Regenerate the data after editing _sessions.yml
ruby parse_sessions.rb          # writes sessions.json

# 2. Preview locally (fetch() is blocked on file://, so serve over HTTP)
python3 -m http.server 8765     # then open http://localhost:8765/

# 3. Deploy: upload index.html + sessions.json to any static host.
```

Features: H2 per day / H3 per time block (collapsible), click a card to expand its
description, bookmark toggle (saved to `localStorage` **and** encoded in the **Share**
link so picks travel between devices), day + "bookmarked only" filters, dark mode by
default, and a **PDF** button that exports your bookmarked sessions.

## Bookmark versioning & stale-link warning

Bookmarks are stored by **position** (each session's array index), which keeps the
Share link tiny but means a link is only valid against the schedule ordering it was
made for. To guard against silent drift:

- `parse_sessions.rb` stamps `sessions.json` with `updated_at` — the last-modified
  date of `_sessions.yml`. Editing the YAML and regenerating bumps it.
- Saved picks record the schedule version they were made against (in `localStorage`),
  and the **Share** link carries it as `&d=YYYY-MM-DD`.
- On load, if the current `updated_at` is **newer** than the version the picks were
  made for, a dismissible banner warns that some bookmarks may now point to different
  talks. Editing any bookmark re-stamps to the current version (clearing the warning);
  dismissing hides it until the schedule changes again.

Because the date bumps on *any* edit, the warning is intentionally conservative — it
can fire even after a safe append-only change. Treat it as "re-check your picks,"
not "your picks are definitely wrong." (Appending new sessions to the **end** of the
YAML never shifts existing ids; only reordering or mid-list inserts do.)

---

## Data schema

Each entry under `sessions:` uses this exact shape and field order:

```yaml
  - title: "Session title"          # quote if it contains a colon or leading punctuation
    date: 2026-11-11                 # ISO YYYY-MM-DD
    day: Wednesday                   # full weekday name, must agree with date
    start: "9:00 AM"                 # 12-hour, always quoted
    duration_min: 60                 # integer minutes
    speakers: [First Last, Other Name]
    location: Gold
    tags: [Track Name, Format, Learning Sequence, Audience Level]
    description: One-line summary, or null if none.
```

- **`tags`** are positional: `[track, format, learning_sequence, audience_level]` where
  present. The first tag (the track) is styled as the accent chip in the UI.
- Missing values → `null` (e.g. `description: null`, or `tags: []`).

---

## Prompt: turn raw talk listings into clean schedule YAML

Paste the prompt below into Claude (or another capable model), then paste the raw,
messy talk data after it. It expands each talk into the schema above and **normalizes
formatting** so the result is valid, uniform, and easy to read. Use it to add new days
or bulk-import talks, then run `ruby parse_sessions.rb`.

~~~text
You convert raw, inconsistently formatted conference-talk listings into a clean YAML
schedule file. Output ONLY the YAML — no prose, no code fences.

TOP OF FILE (emit once):

    conference: <name>
    venue_timezone: <IANA zone + short label, e.g. America/Los_Angeles (PT)>
    session_count: <integer = number of session entries you output>
    tag_note: tags are [track, format, learning_sequence, audience_level] where present
    sessions:

Then one entry per talk, in this EXACT field order:

  - title: ...
    date: ...            # ISO YYYY-MM-DD
    day: ...             # full weekday name; derive it from date and make them agree
    start: "H:MM AM/PM"  # 12-hour clock, ALWAYS double-quoted
    duration_min: N      # integer minutes
    speakers: [Name, Name]
    location: ...
    tags: [Track, Format, LearningSequence, AudienceLevel]
    description: ...      # single line, or the literal null

INDENTATION & LAYOUT (keep it legible):
- Two spaces before each `- title:`; four spaces for the other keys.
- Exactly one blank line between entries; none between keys within an entry.
- Keep the field order above for every entry, even when some values are null.

NORMALIZE / CORRECT BAD FORMATTING:
- Field names: map any synonym to the canonical key — time→start, duration→duration_min,
  presenter/author/host→speakers, room/hall→location, blurb/abstract→description.
- Durations: convert everything to integer minutes. "60m"/"60 min"/"1h"/"1 hour"→60,
  "90 min"/"1.5h"→90, "3 hours"/"180m"→180, "30m"→30.
- Times: convert 24-hour or sloppy times to quoted 12-hour, e.g. 13:00→"1:00 PM",
  "9am"→"9:00 AM".
- Collapse folded/multi-line (`>-`, `|`) or wrapped descriptions into ONE line; trim
  trailing whitespace; keep the original wording and real punctuation (including curly
  apostrophes/quotes). Do NOT invent or embellish content.
- Convert block-style lists (dashed items on their own lines) into inline flow lists:
  `[A, B, C]`.
- De-duplicate tags and speakers while preserving order (e.g. [Panel, Panel]→[Panel]).
- Empty list → `[]`; missing scalar → `null` (unquoted).

QUOTING RULES (so the file is valid YAML and easy to read):
- Double-quote any title or description that contains a colon-space (": "), a leading
  special char (>, |, #, -, *, &, !, %, @, ?, [, {, ", '), or a trailing colon.
- Double-quote any tag or speaker that contains a comma (e.g.
  "Websites, Email & Direct Sales") so it isn't split into two list items.
- `start` is always quoted. `date`, `day`, integers, and `null` are never quoted.

TAGS are positional: [track, format, learning_sequence, audience_level] where known.
Put the primary track FIRST. Omit trailing positions you can't determine rather than
guessing; never pad with empty strings.

If a source value is genuinely missing, use `null` (or `[]`) — do not fabricate. If a
talk is truncated or unreadable in the source, keep what's there verbatim and set the
missing fields to null.
~~~

### Example

**Input (messy):**

```
Andy Weir Interview — interviewer JN Chaney. Fri Nov 13, 4pm, Event Center, 90 min.
Tags: Keynote / Live Education
```

**Output:**

```yaml
  - title: Andy Weir Interview
    date: 2026-11-13
    day: Friday
    start: "4:00 PM"
    duration_min: 90
    speakers: [JN Chaney]
    location: Event Center
    tags: [Keynote, Live Education]
    description: null
```

After pasting the generated entries into `_sessions.yml`, run `ruby parse_sessions.rb`
to refresh `sessions.json`, then reload the page.
