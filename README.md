# Con Schedules

A Hugo site that hosts a personal session-picker for any number of conferences.
Each conference gets its own page with the same UI: day / tag filters, an
in-browser AI "tailor" filter, bookmarks (saved locally **and** encoded in a
compact Share link), dark/light, and a PDF export of your picks. No JS build
step — Tailwind and pdfmake load from CDNs; the page fetches its
`sessions.json` at runtime.

Currently hosted: **Author Nation 2026** (`/author-nation-2026/`) and
**TravellerCON/USA 2026** (`/travellercon-usa-2026/`).

## Layout

```
hugo.toml                          site config; declares the "sessions" JSON output format
content/<slug>/_index.md           one per conference — front matter = that con's settings
data/cons/<slug>.yaml              one per conference — the schedule (source of truth)
layouts/index.html                 landing page listing every con
layouts/con/section.html           the schedule app (rendered once per con)
layouts/con/section.sessions.json  emits /<slug>/sessions.json from data/cons/<slug>.yaml
scripts/                           converters that produce data/cons/*.yaml
```

The `<slug>` of the content directory and the data file **must match** — that's
how the templates find the data.

## Usage

```bash
hugo server            # develop at http://localhost:1313/
hugo                   # build → public/  (deploy that directory to any static host)
```

## Styling

CUBE-style, utility-first CSS on top of vendored [Open Props](https://open-props.style) —
no Tailwind, no inline styles. Hugo's asset pipeline concatenates, minifies and
fingerprints `assets/css/*.css` (`layouts/partials/head-css.html`).

```
assets/css/00-layers.css        @layer base, components, utilities
assets/css/01-open-props.css    vendored, immutable
assets/css/02-tokens.css        palette ladders (50–950) + semantic tokens + type/space/motion aliases
assets/css/03-fonts.css         self-hosted @font-face (Crimson Pro, Lora, Public Sans, IBM Plex Mono → static/fonts/)
assets/css/04-base.css          resets, element defaults, focus ring, reduced motion
assets/css/10-c-*.css           components: button, card, tag, tabs, notice/toast, deck (the slot-deck shell)
assets/css/20-u-*.css           utilities, one intent per file: stack, cluster, pad, surface, eyebrow, type, …
scripts/palette.py              regenerates the palette ladders (fitted in OKLCH to the design anchors)
```

Rules of the road: every design value is a `var()` (semantic token first, Open
Props step second); utilities express intent (`u-stack`, `u-cluster`, `u-eyebrow`)
and are configured through custom properties; BEM blocks only when named,
structured and single-sourced (`.deck` is the one). Breakpoints are `48em` /
`64em`. Dark mode remaps the semantic tokens under `:root.dark`; the theme is
stored site-wide under `cons.theme`.

## Adding a conference

1. **Data** — produce `data/cons/<slug>.yaml` (schema below). Either:
   - hand it a source export and run a converter:
     `python3 scripts/convert_tabletop_events.py scripts/<slug>.events.json data/cons/<slug>.yaml`
     (tabletop.events-style JSON) or
     `python3 scripts/sessions_json_to_yaml.py old-sessions.json data/cons/<slug>.yaml`
     (a legacy `{updated_at, sessions}` JSON export), or
   - use the **prompt in the next section** to have an LLM turn a web page /
     PDF / pasted listing straight into the YAML.
2. **Page** — create `content/<slug>/_index.md`:

   ```yaml
   ---
   title: "Example Con 2027"
   type: con                       # required — selects the schedule template
   conference: "Example Con 2027"  # header + PDF masthead
   subtitle: "Session schedule · Austin · CT"
   city: "Austin, TX"              # shown on the landing page
   startDate: "2027-03-05"         # landing page + sort order (newest first)
   endDate: "2027-03-07"
   tzLabel: "CT"                   # suffix on times in the PDF
   tzLong: "All times Central (CT)"
   storagePrefix: "ex2027"         # localStorage namespace — unique per con, never change it
   pdfFilename: "example-con-2027-schedule.pdf"
   aiPlaceholder: "Describe your interests — e.g. …"
   source: "https://…"             # linked in the footer
   endTags: ["Keynote", "Panel", "Workshop"]   # format-type tags sorted to the END of the tag filter
   ---
   ```
3. `hugo server` — the con appears on the landing page and at `/<slug>/`.

## Data schema (`data/cons/<slug>.yaml`)

```yaml
updated_at: "2026-08-16"       # YYYY-MM-DD; bump on ANY change (drives the stale-bookmark warning)
session_count: 37              # informational
sessions:
  - id: 0                      # 0-based array position — bookmarks & Share links are bit-indexed by id
    event_number: 36           # optional: the organiser's own event id
    title: "Session title"
    date: "2026-10-16"         # ISO, QUOTED (keeps it a string)
    day: Friday                # full weekday, must agree with date
    start: "1:30 PM"           # 12-hour, QUOTED
    duration_min: 240          # integer minutes
    speakers: ["Name", "Name"] # [] if none
    location: "Ben Franklin Room"
    tags: ["RPG", "DGS"]       # first tag = primary track/type (accent chip); [] if none
    description: "One paragraph, single line, or null"
```

Rules of thumb:
- **Bookmarks are positional.** Append new sessions at the end; don't reorder or
  insert mid-list if you want existing Share links to keep pointing at the same
  talks. Bump `updated_at` on every edit so visitors get the "re-check your picks"
  banner.
- Keep the list sorted by date, then start time, then title on first import.
- The **first tag** is styled as the accent chip; put the primary track/type there.

---

## Prompt: turn hosted conference information into `data/cons/<slug>.yaml`

Paste this into Claude (or another capable model), then give it the source —
a schedule web page (URL or pasted text), a PDF programme, a CSV/JSON export, or
a messy pasted list. It returns the YAML file, ready to save.

~~~text
You convert conference schedule information — from a web page, PDF, export file,
or pasted text — into a clean YAML schedule file for a static session-picker
site. Output ONLY the YAML — no prose, no code fences.

INPUT
I will give you the schedule source (URL contents, pasted text, PDF text, or a
JSON/CSV export) plus, if known: the conference name, venue time zone, and any
inclusion filter (e.g. "in-person events only"). If a value is genuinely
missing, use null (or [] for lists). NEVER invent speakers, rooms, times, or
descriptions.

TOP OF FILE (emit once, exactly these keys, in this order)

    updated_at: "<today, YYYY-MM-DD>"
    conference: "<name>"
    venue_timezone: "<IANA zone, e.g. America/New_York>"
    source: "<URL or short description of where the data came from>"
    filter: "<what was included/excluded, or null>"
    session_count: <integer = number of entries you output>
    sessions:

THEN ONE ENTRY PER SESSION, in this EXACT field order

  - id: N                     # 0-based, sequential, in output order
    event_number: N           # organiser's own id/number if there is one, else omit the line
    title: "..."
    date: "YYYY-MM-DD"        # ISO, always double-quoted
    day: Weekday              # full name, derived from date, unquoted
    start: "H:MM AM"          # 12-hour clock, always double-quoted
    duration_min: N           # integer minutes (compute from end - start if only an end time is given)
    speakers: ["Name", "Name"]# [] if none. Presenters/hosts/GMs/panelists all count as speakers.
    location: "..."           # room / hall / table, or null
    tags: ["Primary", "..."]  # see TAGS; [] if none
    description: "..."        # single line, or null

ORDERING
Sort chronologically: date, then start time, then title. Then assign ids
0..N-1 in that order. (Ids are positional; the site's bookmarks depend on them.)

TIMES
- Convert everything to the venue time zone if the source uses another.
- 24-hour or sloppy times → quoted 12-hour: 13:00 → "1:00 PM", "9am" → "9:00 AM",
  "noon" → "12:00 PM".
- Durations to integer minutes: "1h" → 60, "90 min"/"1.5h" → 90, "3 hours" → 180.
  If neither duration nor end time is given, use null.

TAGS
- tags[0] is the PRIMARY classification and is displayed as the accent chip:
  use the track for talk-style conferences, or the event type (e.g. Panel, RPG,
  Miniatures, Workshop, Keynote) when there is no track system.
- Add further tags only when they are useful filters and reused across several
  sessions: format (Panel / Workshop / Keynote), audience level, a series or
  organiser prefix that recurs (e.g. "DGS" for "DGS Presents: …"), a game
  system, a room block. Do NOT tag one-off words.
- Normalise spelling/casing so identical tags are byte-identical; de-duplicate
  while preserving order. Keep tag names short (1–3 words).

DESCRIPTIONS
- Collapse multi-line / wrapped text into ONE line; trim; keep the original
  wording and punctuation (including curly quotes/apostrophes). Do not embellish
  or summarise beyond removing line breaks and obvious scraping junk
  (navigation text, "Read more", ticket buttons, repeated headers).
- If a description contains a double quote, escape it as \" (the value is a
  JSON-style double-quoted YAML string).

FILTERING & DUPLICATES
- Apply any inclusion filter I give you (e.g. drop online-only events). If a
  filter is applied, describe it in the top-level `filter:` key.
- Keep repeated runs of the same event (same title, different time) as separate
  entries — they are separate sessions.
- Drop exact duplicate rows (same title, date, start, location).

QUOTING (so the file is valid YAML)
- title, date, start, location, description, speakers[], tags[], and all
  top-level string values: ALWAYS double-quoted (JSON string rules).
- day, integers, and null: NEVER quoted.
- Lists are inline flow style: ["A", "B"]; empty list is [].

LAYOUT
- Two spaces before "- id:", four spaces for the other keys of an entry.
- Exactly one blank line between entries; none between keys within an entry.
- Same field order for every entry, even when values are null.

If the source is truncated or unreadable in places, keep what is there verbatim
and set the unknown fields to null — never guess.
~~~

### Example

**Input (from a schedule page):**

```
Sat Oct 17 · 1:30 PM–5:30 PM · Ben Franklin Room
DGS Presents: X-Boat Station Theta  (RPG – In-Person)
DGS Presents: X-Boat Station Theta, a MegaTraveller adventure. You are a Scout team …
Characters provided.
```

**Output entry:**

```yaml
  - id: 21
    title: "DGS Presents: X-Boat Station Theta"
    date: "2026-10-17"
    day: Saturday
    start: "1:30 PM"
    duration_min: 240
    speakers: []
    location: "Ben Franklin Room"
    tags: ["RPG", "DGS"]
    description: "DGS Presents: X-Boat Station Theta, a MegaTraveller adventure. You are a Scout team … Characters provided."
```

Save the output as `data/cons/<slug>.yaml`, add `content/<slug>/_index.md`
(see *Adding a conference*), and run `hugo server`.
