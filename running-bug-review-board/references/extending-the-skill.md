# Extending this skill

This skill is designed to grow without rewrites. Four common extensions —
new tracker, new heuristic, new surface, new mode — are additive: copy a
section, fill it in, the agent picks it up on the next session.

This reference is the contributor's map.

## Contents

- Skill anatomy
- Add a new issue tracker
- Add a new triage heuristic
- Add a new surface
- Add a new mode
- Bump the skill version
- Where to ask before contributing
- Style guide for new docs
- Out of scope for v0.2 (and where to start when they're in scope)

## Skill anatomy

```
plugins/running-bug-review-board/
├── .claude-plugin/plugin.json          # version + description + keywords
└── skills/running-bug-review-board/
    ├── SKILL.md                        # entry point (~500 lines)
    ├── references/                     # loaded on demand
    │   ├── workflow.md
    │   ├── discovering-the-app.md
    │   ├── test-plan.md
    │   ├── test-accounts.md
    │   ├── session-hygiene.md
    │   ├── browser-playbook.md
    │   ├── computer-use-playbook.md
    │   ├── parallel-coordinator.md
    │   ├── sequential-wrapup.md
    │   ├── bug-filing.md
    │   ├── gate-merge.md
    │   ├── html-report-style-guide.md
    │   ├── issue-trackers.md
    │   ├── brb-interactive.md
    │   ├── triage-heuristics.md
    │   ├── ios-simulator-playbook.md
    │   ├── extending-the-skill.md      # ← you are here
    │   └── templates/
    │       ├── bug-report.md
    │       ├── run-report.md
    │       ├── coordinator-merge.md
    │       ├── test-plan.md
    │       ├── shard-prompt.md
    │       ├── sequential-prompt.md
    │       ├── brb-interactive-prompt.md
    │       ├── brb-minutes.md
    │       ├── qa-config.example.json
    │       └── html-report/
    │           ├── README.md
    │           ├── assets.css
    │           ├── index.html
    │           ├── bug.html
    │           └── run.html
    └── scripts/
        ├── scaffold-qa.sh
        ├── bugs-needing-sync.sh
        └── bugs-needing-pull.sh
```

### Rules of composition

- **SKILL.md** stays under 500 lines. It's the discovery surface — the
  agent reads it on every activation. Detail lives in references.
- **Frontmatter descriptions stay short.** Codex rejects `description`
  values over 1,024 characters and may shorten much smaller descriptions
  to fit its skills metadata budget. Treat the description as routing
  metadata: front-load trigger words, keep it under ~350 characters when
  practical, and move procedure details into the body or references.
- **References** are loaded on demand. Keep each under 500 lines too;
  split if a topic grows.
- **Progressive disclosure.** References can link to other references
  (one level deep). Don't build trees.
- **Templates are copy-paste payloads.** They're not loaded as
  knowledge; they're the literal content the agent writes into the
  target repo.
- **Scripts stay small.** Tiny helpers that enumerate work. The agent
  does the action.

## Add a new issue tracker

1. Open [issue-trackers.md](issue-trackers.md).
2. Copy any `## Adapter — <Name>` section to a new section at the end
   (or alphabetized).
3. Fill in:
   - Install (one-liner + link)
   - Auth (env var / OAuth flow / token reference)
   - Create-bug shape (CLI or MCP tool call with full payload)
   - Status-flip shape (how to change status from outside)
   - Read shape (how to pull for bi-directional sync)
   - Label / priority map (BRB's P0 / P1 / P2 → tracker's equivalent)
   - Dedupe key (a new front-matter row in `bug-report.md`)
   - Anti-patterns
4. Add the type string to the **Discovery ceremony's user prompt** in
   [issue-trackers.md](issue-trackers.md) — option 6+ on the list.
5. Add the type string + per-tracker fields to
   [templates/qa-config.example.json](templates/qa-config.example.json).
6. Add a new front-matter row to
   [templates/bug-report.md](templates/bug-report.md):
   ```
   | **Tracker / <Name>** | *(<ID format> — fill after sync; blank if N/A)* |
   ```
7. Add corresponding `{{TRACKER_<NAME>}}` slots to
   [templates/html-report/bug.html](templates/html-report/bug.html) (model
   on the existing Linear / GitHub / Jira slots).

That's it. The agent reads the new section on its next discovery
ceremony.

## Add a new triage heuristic

1. Open [triage-heuristics.md](triage-heuristics.md).
2. Add a new entry under **Heuristics catalog** with:
   - Name (kebab-case)
   - Signal (1–2 sentences)
   - Cite (what text to show the user)
   - Proposed action (pick one of merge / link / consolidate / defer or
     define a new one in **Confirmed-action contract**)
3. Add the heuristic name to the default
   `triage.enabledHeuristics` list in
   [templates/qa-config.example.json](templates/qa-config.example.json).
   (Heuristics not in `enabledHeuristics` are skipped; if the field is
   absent, all are enabled.)
4. No code changes. The agent applies the new heuristic on next BRB.

## Add a new surface

A "surface" is a place users interact with the app — browser viewport,
iPhone Mobile Safari, iPad Mobile Safari, native macOS, Apple Watch,
Android, etc.

1. If the surface fits in an existing playbook
   ([browser-playbook.md](browser-playbook.md),
   [ios-simulator-playbook.md](ios-simulator-playbook.md)): add a row
   to that playbook's recommended-stack table.
2. If the surface needs its own playbook: create
   `references/<surface>-playbook.md`. Use the iOS playbook as a model
   (pre-flight + universal core + companion ladder + recommended stacks
   + workflow patterns + graceful degradation + credit).
3. Add a row to the **Mode picker** table in `SKILL.md`.
4. Add per-platform config to
   [templates/qa-config.example.json](templates/qa-config.example.json):
   ```jsonc
   "platforms": {
     "<surface>": { "enabled": false, … }
   }
   ```
5. If the surface has its own evidence subdirectory, document the
   convention (e.g. `assets/BUG-NNN/android/`) and add a
   `{{<SURFACE>_SCREENSHOTS}}` block to
   [templates/html-report/bug.html](templates/html-report/bug.html).

## Add a new mode

A "mode" is a top-level workflow — Parallel Coordinator, Sequential
Wrap-up, Interactive BRB, etc.

1. Create `references/<mode>.md`. Use
   [brb-interactive.md](brb-interactive.md) as a model: when to use,
   inputs, numbered workflow, rules, outputs, definition of done,
   anti-patterns.
2. Add a row to the **Mode picker** table in `SKILL.md`.
3. If the mode needs its own agent prompt, add
   `templates/<mode>-prompt.md` (model on
   [templates/brb-interactive-prompt.md](templates/brb-interactive-prompt.md)).
4. If the mode produces a new artifact type, add it to the
   **Deliverables per pass** table in `SKILL.md`.
5. Reference the new mode from
   [workflow.md](workflow.md) (Step 5 "Choose mode").

## Bump the skill version

Treat any change that requires consumers to re-read the documentation
(or that breaks an existing template's contract) as a version bump.

### Checklist

- [ ] `plugins/running-bug-review-board/.claude-plugin/plugin.json` →
      `version`.
- [ ] `.claude-plugin/marketplace.json` → matching plugin version +
      description.
- [ ] `references/html-report-style-guide.md` → update the
      `<!-- skill:running-bug-review-board vX.Y -->` marker rule.
- [ ] `references/templates/html-report/*.html` → update the marker in
      each file.
- [ ] `CHANGELOG.md` → new dated section. Credit upstream projects /
      contributors by name.
- [ ] `README.md` → update the "What's new" callout at the top + the
      skill list table if relevant.
- [ ] `SKILL.md` frontmatter description if the surface area changed.
- [ ] Validate Codex-compatible metadata before tagging:
      ```bash
      python3 scripts/validate-skill-metadata.py
      ```
- [ ] **Push an annotated git tag.** GitHub Releases only update when
      a `v*` tag is pushed (the `.github/workflows/release.yml`
      workflow fires on tag push, builds `running-bug-review-board.zip`,
      and attaches it to a new Release). Without this step the
      manifests say the new version but GitHub Releases keeps showing
      the old one.
      ```bash
      git tag -a vX.Y.Z -m "vX.Y.Z — <one-line summary>"
      git push origin vX.Y.Z
      ```
- [ ] Verify the workflow ran and the Release was created:
      ```bash
      gh run list --limit 2
      gh release view vX.Y.Z
      ```

### Semver rules of thumb for this skill

- **Patch (x.y.Z)**: docs clarifications, typo fixes, scaffolder bug
  fixes, no contract changes.
- **Minor (x.Y.0)**: new reference, new template, new mode, new
  surface, new heuristic, new tracker adapter, new script. Existing
  consumers don't have to migrate.
- **Major (X.0.0)**: renaming or removing front-matter rows, changing
  the HTML version marker meaning, breaking a script's CLI.

### Backward compatibility rules

- **`qa-config.json`** is forward-compat. Unknown top-level fields are
  ignored. New fields go alongside existing ones; never rename. The
  `version` integer tracks schema generation.
- **Bug front-matter** only adds rows. Existing rows keep their labels
  forever. If a row's *meaning* needs to change, add a new row with a
  new label and document the migration in the CHANGELOG.
- **HTML report** version marker is the migration anchor. Old reports
  with an older marker should still render (the stylesheet is
  backward-compatible by design — additions are net-new classes).
- **Templates** can change freely; consumers re-scaffold to pick up
  improvements.

## Where to ask before contributing

- For a new tracker: confirm the upstream MCP / CLI / API is stable
  enough to rely on.
- For a new heuristic: collect 3+ real-world examples where it would
  have helped, before writing.
- For a new surface: confirm there's at least one community skill /
  tool you can cite as the "input driver" — we orchestrate, we don't
  replace.
- For a new mode: confirm the mode is genuinely separable from existing
  ones (not just a variant of Sequential Wrap-up).

If unsure, open an issue on
[rayfernando-skills](https://github.com/RayFernando1337/rayfernando-skills)
with a one-paragraph proposal before writing the reference.

## Style guide for new docs

- **Imperative voice**, second person ("Run", "Copy", "Confirm").
- **Frontmatter description** is third person ("Runs a real-user QA
  pass...").
- **Examples from real projects** when possible. Name the project (and
  thank the maintainer) if it's shareable.
- **No time-sensitive copy.** Instead of "as of 2026" use "verified at
  v0.2 release date — check the project's README".
- **One screen of text per reference.** Split if it grows past ~500
  lines.
- **Cross-link references** with relative paths. Test the links before
  pushing.

## Out of scope for v0.2 (and where to start when they're in scope)

- **Bi-directional tracker sync for tracker-originated bugs (auto-import).**
  Defaults to `"ask"` unless the config says otherwise. To turn on `"create"`, add a contract
  section to [issue-trackers.md](issue-trackers.md) covering what local
  metadata to invent (Test ID? gate item?) when the tracker doesn't have
  them.
- **Embeddings-backed heuristics.** Heuristics are explainable
  text patterns. To add fuzzy matching: introduce
  `triage.fuzzy: true | "<model>"` and document the model dependency.
- **A `qa` umbrella CLI.** Scripts are tiny shell helpers. To
  bundle, treat the umbrella as a separate published package and link
  to it from `SKILL.md`.
- **CI workflow that lints templates and dry-runs the HTML render.**
  If the consuming repository has no such check: a GitHub Action that runs
  `bash -n scripts/*.sh`, validates `qa-config.json` against a JSON
  schema (would also need to ship the schema), and renders the
  skeletons against a fixture repo.
- **Evals folder** (à la AXe / serve-sim) with copy-paste prompts for
  agent quality.

When the workflows settle, these become natural follow-ups.
