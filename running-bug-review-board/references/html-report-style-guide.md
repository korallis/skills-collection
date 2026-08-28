# HTML report style guide — v0.3

The QA agent generates an HTML report (`docs/qa/report/`) from the
existing markdown bug and run files. **Markdown stays the source of
truth.** HTML is the read-only view layer the team scans during triage.

This guide encodes the design language so any agent that follows it
produces consistent, scannable output. The agent reads this file,
opens the skeleton templates in
[templates/html-report/](templates/html-report/), and writes
`docs/qa/report/index.html` + `bugs/BUG-NNN.html` + `runs/<slug>.html`.

## Design philosophy

**Zite + Dieter Rams. Less, but better.**

The report reads like a magazine, not like a Kanban board.
Decoration is gone. Typography does the work that colored chips and
pills did in v0.2.

| Principle | What it means here |
|-----------|---------------------|
| **Useful before pretty** (Rams 1) | Every element answers a triage question. Nothing decorative. |
| **Honest** (Rams 6) | Severity isn't dressed up with red/orange/yellow. P0 is the word "P0", set in the eyebrow. |
| **Unobtrusive** (Rams 5) | Chrome disappears. Content sings. |
| **As little design as possible** (Rams 10) | One ink colour for body. One quiet accent (terracotta) for links. Hairline rules for separation. That's it. |
| **Editorial weight** (Zite) | A reading column ~640px wide. Serif pull-quotes for impact. Display type for verdicts and titles. |
| **The eye reads top-down** | Title, then deck, then impact, then prose. Metadata goes to a quiet right rail on desktop, hidden under the title on mobile. |

What we explicitly stopped doing in v0.3:

- ❌ Coloured priority chips (`chip-p0` etc.)
- ❌ Coloured status pills with dots
- ❌ Coloured verdict badges
- ❌ Card grids with shadows
- ❌ A three-column Kanban for the open bug board
- ❌ Tracker tags as colourful pills
- ❌ "Filter by colour" affordances

What we do instead:

- ✅ Priority is the word `P0` in the eyebrow line above the title
- ✅ Status is a word in the same eyebrow (`Open`, `In progress`)
- ✅ Verdict is a single word — `YES` or `NO` — in display type
- ✅ Open bugs are a magazine list, ordered P0 then P1 then P2
- ✅ Hairline rules separate sections; no cards
- ✅ One accent colour, used only on interactive things
- ✅ Filter affordances are quiet `<details>` elements with checkbox lists

## Information hierarchy contract

This is the order the engineer's eye lands on a bug. **Templates
must preserve this order** so a reviewer can scan a bug in seconds:

1. **Eyebrow** — small caps line with `Priority · Phase · Status · Tracker`
2. **Title** — what is this? (display type)
3. **Deck** — the one-sentence Summary, set in serif
4. **Impact** — what does a user experience if this ships unfixed?
   (a pull-quote with a vertical hairline rule on the left)
5. **Actual** — what's happening now? (prose)
6. **Expected** — what should happen? (prose)
7. **Risk to fix** — engineer's marginal note. Hidden when empty.
8. **Steps to reproduce** — numbered list with a monospace gutter
9. **Evidence** — console errors first (cheap to read), then
   server / DB, then network, then screenshots (bulkiest, scroll for it)
10. **Notes** — anything else the filer noted
11. **Triage log** — the bug's history of decisions

The right rail (desktop only) holds Test ID, Gate, Reported, Fixed in,
Verified by, tracker IDs, last-synced timestamp, Duplicate-of /
Related links. None of that crowds the reading column.

## Output layout

```
docs/qa/report/
├── index.html              # dashboard
├── assets.css              # shared stylesheet (canonical copy below)
├── bugs/
│   └── BUG-NNN.html        # one per bug-report markdown
└── runs/
    └── <slug>.html         # one per run-report or coordinator-merge markdown
```

The folder sits next to the markdown sources under `docs/qa/`, so
links between pages stay short and `assets/BUG-NNN/*.png` paths
resolve with `../../bug-reports/assets/BUG-NNN/...`.

## Versioning

Every generated page carries
`<!-- skill:running-bug-review-board v0.3 -->` near the top of `<head>`.
Later agents look for this marker to decide whether to extend or
rewrite.

If a marker doesn't match (someone hand-edited the file or the version
is older): write to `index.next.html` (or `bugs/BUG-NNN.next.html`) and
tell the user to diff. **Never silently overwrite**.

## Design tokens (canonical)

The full token set lives in
[templates/html-report/assets.css](templates/html-report/assets.css) —
the agent copies it verbatim to `docs/qa/report/assets.css` on every
regenerate. Summary:

### Colour — almost monochrome

| Token | Light | Dark | Where |
|-------|-------|------|-------|
| `--ink` | `#1A1A1A` | `#ECEAE3` | All body text. |
| `--paper` | `#FAFAF7` warm off-white | `#131311` near-black | Page background. |
| `--rule` | `#D8D6D0` | `#2E2D2A` | Hairline separators. |
| `--mute` | `#6B6864` | `#908C84` | Eyebrow, metadata, captions. |
| `--soft` | `#F2F0EA` | `#1B1B18` | Pre code blocks, evidence frames. |
| `--accent` | `#A5391A` deep terracotta | `#E08263` lifted terracotta | Links, CTA underlines, the period after `NO`. **The only saturated colour on the page.** |
| `--quote` | `#2A2A2A` | `#F4F2EB` | Pull-quotes and decks. |
| `--warn-ink` | `#3A1A0A` | `#F4D9C6` | The `P0` prefix in the eyebrow. Not a swatch — an ink shift. |

We do not use systemRed / systemOrange / systemYellow / systemGreen
anywhere. Priority and status are typographic.

### Typography — magazine register

```css
--font-display: ui-sans-serif, -apple-system, "SF Pro Display",
                BlinkMacSystemFont, "Helvetica Neue", Helvetica, Arial,
                sans-serif;
--font-text:    ui-sans-serif, -apple-system, "SF Pro Text",
                BlinkMacSystemFont, "Helvetica Neue", Helvetica, Arial,
                sans-serif;
--font-serif:   ui-serif, Charter, "Iowan Old Style", "Times New Roman",
                Georgia, serif;
--font-mono:    ui-monospace, "SF Mono", Menlo, Monaco, "Cascadia Mono",
                monospace;
```

Display headlines use the display stack, body uses text, decks and
pull-quotes use serif, IDs and code use mono.

### Scale — display type for verdicts, reading type for prose

| Token | Size | Use |
|-------|------|-----|
| `--size-display-xl` | clamp(40, 6vw, 64) | Verdict word `YES` / `NO` |
| `--size-display-l`  | clamp(28, 4vw, 40) | Article title on bug detail |
| `--size-display-m`  | clamp(22, 3vw, 28) | Article title in the list |
| `--size-deck`       | clamp(18, 2vw, 21) | Deck, impact pull-quote |
| `--size-headline`   | 17 | Section headings |
| `--size-body`       | 17 | Prose |
| `--size-meta`       | 13 | Metadata, footnotes |
| `--size-micro`      | 11 | Uppercase eyebrow |

### Rhythm — 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 96

Use `--s-1` through `--s-9`. Generous whitespace is the point.

### Layout — reading column always

| Token | Value | Why |
|-------|-------|-----|
| `--col-read` | 640px | Comfortable reading line length (~70ch in our typeface). |
| `--col-rail` | 220px | Right-rail metadata on desktop only. |
| `--gutter` | clamp(20, 4vw, 48) | Page padding. |

On mobile: single column. On desktop (≥1024px): the bug detail page
adds the right rail (`.read.has-rail`); the dashboard stays single
column at all widths.

## Component recipes

Each component has a fenced HTML snippet the agent copies and fills.
See [templates/html-report/](templates/html-report/) for full skeleton
files that wire these together.

### Page chrome

```html
<header class="masthead">
  <div class="masthead-inner">
    <h1 class="masthead-title"><a href="./">{TITLE}</a></h1>
    <p class="masthead-meta">
      <time datetime="{ISO}">{HUMAN}</time> · <a href="../">qa/</a>
    </p>
  </div>
</header>
```

A hairline rule below, no card. The title is small caps so the
verdict that follows can take the visual top spot.

### Verdict — display type, not a badge

```html
<article class="verdict">
  <p class="eyebrow">Phase 2 — sessions-scheduling</p>
  <h2 class="verdict-word is-no">NO</h2>
  <p class="verdict-line">
    Two P0 bugs block sign-off; sequential wrap-up is scheduled.
  </p>
  <a class="verdict-action" href="runs/COORDINATOR-MERGE-2026-05-27.html">
    Read the merge
  </a>
</article>
```

The class `is-no` appends a terracotta full-stop after the word `NO`
— a quiet, final refusal, not an alarm. `is-yes` omits the stop and
leaves the word standing on its own.

### Eyebrow — the metadata line above a title

```html
<p class="eyebrow">
  <span class="pri">P0</span><span class="sep">·</span>Phase 2<span class="sep">·</span>Open<span class="sep">·</span>LIN-1244
</p>
```

All small caps, all letter-spaced, all `--mute` except the `.pri`
which uses `--warn-ink` for a slight ink shift. The `·` separator is
the rule colour.

### Bug list item — a magazine article preview

```html
<li class="bug-list-item"
    data-priority="P0" data-status="open" data-phase="2">
  <a class="bug-list-link" href="bugs/BUG-007.html">
    <p class="bug-list-meta">
      <span class="pri">P0</span><span class="sep">·</span>Phase 2<span class="sep">·</span>Open<span class="sep">·</span>LIN-1244
    </p>
    <h3 class="bug-list-title">Stale invite poisons fresh-user signup</h3>
    <p class="bug-list-impact">
      A user who opened an invite link, abandoned it, then returned later and
      signed up without one is silently joined to the old group.
    </p>
  </a>
</li>
```

Each list item is an article preview. The list is rendered three
times on the dashboard — one ordered list per priority group, headed
by a small-caps divider `P0 — 3 open`. No Kanban columns.

### Priority group header

```html
<h3 class="bug-group-head">P0 <span class="count">— 3 open</span></h3>
<ol class="bug-list" data-priority-group="P0">…</ol>
```

A bold underline rule sits beneath the heading to separate priority
sections. The count is muted.

### Article title + deck (bug detail)

```html
<header class="article-header">
  <p class="eyebrow">
    <span class="pri">P0</span><span class="sep">·</span>Phase 2<span class="sep">·</span>Open<span class="sep">·</span>LIN-1244
  </p>
  <h1 class="article-title">Stale invite poisons fresh-user signup</h1>
  <p class="article-deck">
    A returning visitor's stale sessionStorage hijacks fresh-user signup
    when the URL has no invite parameter.
  </p>
</header>
```

### Impact — a pull-quote

```html
<aside class="article-impact">
  <p class="eyebrow">Impact</p>
  <p>
    Anyone who briefly considered an invite from a co-worker can be
    silently joined to that group days later, without their consent
    or knowledge.
  </p>
</aside>
```

Set in serif, with a 2px ink rule on the left edge. Hidden if the
markdown has no Impact section.

### Risk to fix — quiet engineer's marginal note

```html
<aside class="article-risk">
  <p class="eyebrow">Risk to fix</p>
  <p>
    Local — the invite-resolution code path is a single function in
    convex/invites.ts. Low blast radius; covered by integration tests.
  </p>
</aside>
```

Set in a soft tinted block with a `--rule`-colour left bar. Often
empty at file time; populated during the BRB by the engineer.
**Hidden when empty** — never displayed as a placeholder.

### Steps to reproduce

```html
<ol>
  <li>Open incognito; navigate to /sign-up?invite=ABC123.</li>
  <li>Abandon the page without finishing the signup.</li>
  <li>Open a new tab; navigate to /sign-up (no parameter).</li>
  <li>Complete the signup with a fresh email.</li>
  <li>Observe the user lands inside the ABC123 group.</li>
</ol>
```

The CSS turns these into a leading-zero numbered list rendered in
monospace in a left gutter, with the step text in the reading
typeface.

### Evidence

Console first, server / network second, screenshots last. Each block
has a small-caps heading. The screenshot gallery uses CSS Grid
`grid-template-columns: repeat(auto-fit, minmax(220px, 1fr))` and tiles
have a hairline border, no shadow.

### Right rail — desktop only

```html
<aside class="read-rail">
  <div class="rail-block">
    <dt>Test ID</dt>
    <dd><code>P2-C1</code> · Gate 2.4</dd>
  </div>
  …
</aside>
```

Hidden on mobile (no grid columns). Each block has small-caps `dt`
and reading-typeface `dd`, separated by a hairline rule.

### Recent runs — quiet list

```html
<li class="runs-list-item">
  <a class="runs-list-link" href="runs/COORDINATOR-MERGE-2026-05-27.html">
    <span class="runs-list-when"><time datetime="2026-05-27">2026-05-27</time> · Phase 2</span>
    Two P0 bugs block sign-off.
  </a>
  <span class="runs-list-counts">
    <span class="v-no">NO</span> · 2 / 3 / 5
  </span>
</li>
```

`v-yes` and `v-no` lift the word slightly above the count line, with
the accent colour reserved for `NO`.

### Filter bar — text affordances

```html
<nav class="filter-bar" aria-label="Filter">
  <details class="filter">
    <summary>Priority</summary>
    <label><input type="checkbox" data-filter="priority" value="P0" checked> P0</label>
    <label><input type="checkbox" data-filter="priority" value="P1" checked> P1</label>
    <label><input type="checkbox" data-filter="priority" value="P2" checked> P2</label>
  </details>
  …
</nav>
```

Open state turns the summary accent-coloured. Checkboxes use
`accent-color: var(--ink)` so they sit in the same monochrome palette.

### Thumb zone — mobile only

```html
<nav class="thumb-zone" aria-label="Mobile actions">
  <a href="runs/COORDINATOR-MERGE-2026-05-27.html">Read the merge →</a>
</nav>
```

A sticky bottom shelf with one accent-underlined action. Hidden on
tablet+ so it doesn't crowd the desktop reading column.

## Mobile-first rules

- **Single column always on mobile.** No right rail. No Kanban.
- **Title is the first thing the eye hits.** Don't put a brand bar above
  it that takes up the fold.
- **Thumb-zone for the primary action.** On phones, duplicate the
  verdict CTA as a sticky bottom bar so the user can read the merge
  doc without scrolling back up.
- **`padding-left/right: clamp(20px, 4vw, 48px)`** — generous gutters
  on all sides.
- **No hover-only affordances.** Anything that needs hover gets a
  visible underline first.

## Desktop rules

- **Reading column stays 640px wide.** Don't widen prose just because
  the viewport allows it.
- **Right rail at ≥1024px** for bug detail pages. Quiet metadata
  separated by hairlines.
- **Generous top padding** (`--s-7`) so the verdict has air around it.

## Accessibility

- Contrast ≥ 7:1 for body text on `--paper`. The terracotta accent
  has ≥ 4.8:1 against `--paper` for links.
- Every priority and status pairs its colour with a label so colour
  isn't the signal. (Here colour barely is the signal anyway.)
- `:focus-visible` outlines use `--accent` at 2px, offset 3px.
- `prefers-reduced-motion: reduce` disables all transitions.
- The print stylesheet drops accent colour to black, removes
  decorative borders, and keeps each bug on its own page.

## Rendering rules

- **Escape all user-supplied text** (bug titles, summaries, body,
  console errors). HTML entity escape; never trust the markdown.
- **Image paths** are relative from the report folder back into the
  existing assets folder: `../../bug-reports/assets/BUG-{NNN}/...`.
  Don't copy; reference in place.
- **Strip secrets** from console blocks per `bug-filing.md`'s rules —
  re-apply on render in case the markdown contains stale tokens.
- **Preserve the version marker** when re-rendering. If the existing
  file's marker doesn't match v0.3 (or has been removed), write to
  `index.next.html` / `bugs/BUG-NNN.next.html` and tell the user to
  diff.
- **Regenerate the whole `docs/qa/report/` folder each pass.** It's a
  view, not a state store. Old pages for deleted bugs disappear.
- **Always rewrite `assets.css`** from the canonical version in
  [templates/html-report/assets.css](templates/html-report/assets.css).

## When the agent is asked to "refresh the report"

1. Read `docs/qa/qa-config.json` for `report.outputDir` and
   `report.title` (defaults: `docs/qa/report` and "QA Report").
2. Read every markdown bug file (skipping `_template.md`), every run
   report, and the latest coordinator merge.
3. Write `assets.css` from the canonical template.
4. For each bug, render `bugs/BUG-{NNN}.html` from
   [templates/html-report/bug.html](templates/html-report/bug.html).
   Substitute the `{{TOKEN}}` placeholders with HTML-escaped values
   from the parsed markdown. Suppress conditional blocks
   (`{{#NAME}}…{{/NAME}}`) when `NAME` is empty.
5. For each run + merge, render `runs/<slug>.html` from
   [templates/html-report/run.html](templates/html-report/run.html).
6. Render `index.html` from
   [templates/html-report/index.html](templates/html-report/index.html).
   The bug list is rendered three times — once per priority group, P0
   first — by concatenating the
   `bug-list-item` snippet per bug.
7. Print a one-line summary: "Wrote N bug pages, M run pages, index
   updated. Open `docs/qa/report/index.html`."

## Notes on the bug template

The HTML report's information hierarchy is set by what's available in
the markdown front-matter and body sections. v0.3 added two new
sections to [templates/bug-report.md](templates/bug-report.md):

- **Impact** — what does a user experience if this ships unfixed?
  Filed by the QA agent. Rendered as a serif pull-quote.
- **Risk to fix** — engineer's marginal note about the difficulty
  / blast radius of fixing. Usually empty at file time; populated
  during the BRB. Rendered as a soft tinted aside. Hidden when empty.

Old bugs without these sections render gracefully: the pull-quote
and aside both disappear, and the eye flows straight from the deck
into Actual / Expected.

## Why this redesign

v0.2 used coloured chips and pills to communicate priority and
status. Two problems with that:

1. **They drew the eye away from the text.** A reviewer trying to
   scan ten open bugs got pulled into a colour pattern instead of
   the prose of each title.
2. **They felt cheap.** A row of red/orange/yellow swatches on the
   side of a card reads like a status board, not a magazine of
   considered bug reports.

v0.3 removes them entirely. Priority is the word `P0` in small caps;
status is the word `Open`. The eye reads the title first, the impact
second, and only checks the priority when it needs to. Triage
decisions get made on the text, not the swatch.

## Extending the style guide

To add a new component (e.g. an "owner badge" once tracker assignees
are pulled), add a row to the **Component recipes** section, document
the markup, and add the CSS in `assets.css`. Bump the version marker
if the change breaks an existing layout. See
[extending-the-skill.md](extending-the-skill.md).
