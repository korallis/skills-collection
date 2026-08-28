# Triage heuristics — pattern-based suggestions

When a bug corpus grows past a handful of entries, the human cost of
spotting duplicates and clusters gets expensive. The agent already reads
markdown bug files competently. This reference teaches it **what to look
for** and **how to present what it finds** so a Bug Review Board (BRB)
session opens with a curated Suggestions card instead of a flat list.

The agent **suggests**; the user **decides**. There is no auto-merge.
Every suggestion cites a named heuristic with text evidence so the user
always sees *why* something was flagged.

## Contents

- When the agent runs heuristics
- What the heuristics are NOT
- Heuristics catalog
- How the agent presents suggestions
- Suggestions (4 clusters across 9 bugs)
- Confirmed-action contract
- Rejected-suggestion memory (lightweight)
- Disabling a heuristic
- Adding a new heuristic
- Anti-patterns

## When the agent runs heuristics

| When | Default | Configured via |
|------|---------|----------------|
| Start of every interactive BRB session | **ON** | `triage.runHeuristicsOnBRBStart` |
| Auto QA pass, before writing a new `BUG-NNN.md` | **OFF** | `triage.runHeuristicsOnFile` |
| On user request ("find duplicates", "are these related?") | always | — |

The auto-pass default is OFF so the pass stays fast. Flip it on if you'd
rather the agent stop on every probable duplicate and ask "file new, or
update BUG-007?"

## What the heuristics are NOT

- Not an LLM API call to a third-party service.
- Not embeddings or vector search.
- Not a confidence score.

They are named text patterns the agent runs by reading the markdown.
Every suggestion is explainable.

## Heuristics catalog

Each entry: **name**, **signal**, **cite** (text evidence to show the
user), **proposed action**.

### `same-suspect-file`

Two or more bugs name the same file path in **Suggested fix area**
(Notes section) or anywhere in the **Steps to reproduce**.

- **Cite:** the matching path string.
- **Action:** "link as related". If also `steps-prefix-overlap` fires,
  upgrade to "merge as duplicate".

### `steps-prefix-overlap`

Two bugs share the first **≥ 3 numbered steps** verbatim (case- and
whitespace-insensitive). The steps must include at least one
URL/action, not three lines of setup like "open the app".

- **Cite:** the matching steps as a numbered list.
- **Action:** "merge as duplicate" (default), or "link as related" if
  the divergence after step 3 looks like a different root cause.

### `same-persona-surface-outcome`

Two bugs share **persona** + **starting URL** + **failure verb**
("redirect", "401", "blank page", "no error toast").

- **Cite:** the matching trio in plain prose.
- **Action:** "merge as duplicate" or "link as related".

### `same-console-error`

Two bugs contain a verbatim console error string (≥ 20 chars, not a
generic message like `TypeError`). Match against the **Evidence →
Console errors** block.

- **Cite:** the error string.
- **Action:** "merge as duplicate" — almost certainly same code path.

### `same-test-id`

Multiple bugs file against the same **Test ID** (e.g. `P2-C1`).

- **Cite:** the Test ID + the bug count.
- **Action:** "consolidate — pick the highest-evidence bug as canonical;
  mark the others duplicate of it."

### `phase-cascade`

A P0 in an earlier phase that touches the same surface as multiple P1s
in the current phase.

- **Cite:** the earlier P0's title + the current-phase P1s' titles.
- **Action:** "block the current-phase P1s until the earlier P0 is
  verified. The P1s may resolve on their own."

### `cosmetic-cluster`

Three or more **P2** bugs on the same surface (matching by starting URL
or by a shared page name in their titles).

- **Cite:** the surface + the bug count.
- **Action:** "consolidate into one polish bug. Title: '<surface> polish
  — N issues'. Link the originals as related."

### `regression-marker`

Bug **Summary** or **Notes** contains a phrase matching one of:

- "regression of BUG-NNN"
- "worked in last QA run"
- "regressed since <commit / phase>"
- "was passing in <prior pass>"

- **Cite:** the matching phrase + the prior bug ID if named.
- **Action:** "link to prior bug (`Related`) and flag in the regression
  matrix of the next merge doc."

### `same-owner`

Multiple open bugs assigned to the same engineer in the tracker (read
during the bi-directional pull — see
[issue-trackers.md](issue-trackers.md)).

- **Cite:** the owner name + the bug IDs.
- **Action:** "batch in their next 1:1; consider whether one root cause
  is producing multiple symptoms."

## How the agent presents suggestions

The agent emits **one Suggestions card** per run (BRB or auto pass).
Inside the card, group rows by proposed action so the user can scan
"things to merge" → "things to link" → "things to defer".

Example (markdown the agent might render in chat or in BRB minutes):

```
## Suggestions (4 clusters across 9 bugs)

### Merge as duplicate
- **BUG-012 → BUG-007**
  Heuristics: same-suspect-file (convex/invites.ts),
  steps-prefix-overlap (3 steps),
  same-console-error ("ConvexError: invite not found").
  Confirm? [merge / reject]

### Link as related
- **BUG-014 ↔ BUG-007**
  Heuristic: same-persona-surface-outcome
  (admin + /sign-up?invite=… + redirect).
  Confirm? [link / reject]

### Consolidate
- **BUG-021, BUG-022, BUG-024** (P2 cluster on /settings/notifications)
  Heuristic: cosmetic-cluster (3 P2s, same surface).
  Proposed: file BUG-025 "Notifications settings polish — 3 issues" and
  mark the originals duplicate of BUG-025.
  Confirm? [consolidate / reject]

### Engineering owner pattern
- BUG-007, BUG-014, BUG-019 are all assigned to @engineer in Linear.
  Heuristic: same-owner.
  No action — surface for awareness; flag in their next 1:1.
```

## Confirmed-action contract

When the user confirms a suggestion, the agent:

1. **Merge as duplicate.** Loser bug's `Status` flips to `duplicate`.
   Front-matter gains `Duplicate of: BUG-XXX`. Triage log adds:
   `<date> | <user> | Marked duplicate of BUG-XXX (heuristics: …)`.
   Winner bug's `Linked bugs (related)` gains the loser's ID.
2. **Link as related.** Both bugs' `Linked bugs (related)` front-matter
   rows are updated. No status change. Both Triage logs add:
   `<date> | <user> | Linked as related to BUG-XXX (heuristic: …)`.
3. **Consolidate.** Agent files a new `BUG-NNN` per
   [bug-filing.md](bug-filing.md) with a summary stitched from the
   originals. Each original's status flips to `duplicate` with
   `Duplicate of: BUG-NNN`.
4. **Defer cluster.** Every bug in the cluster flips to `deferred` with
   the same target phase. Triage log records the BRB decision.
5. **Reject.** No change. The suggestion is recorded in the BRB minutes
   as `rejected by <user>` so it doesn't keep re-appearing.

## Rejected-suggestion memory (lightweight)

To stop the same rejected suggestion from re-firing every BRB, record
rejections in the bug's Triage log:

```
2026-05-27 | jane | BRB: rejected suggestion "merge into BUG-007"
            (heuristic: steps-prefix-overlap; reason: different code path)
```

On the next BRB, the agent reads Triage logs and skips suggestions whose
heuristic name + counterpart bug match a prior rejection.

## Disabling a heuristic

In `qa-config.json`:

```jsonc
"triage": {
  "enabledHeuristics": [
    "same-suspect-file",
    "steps-prefix-overlap",
    "same-persona-surface-outcome",
    "same-console-error",
    "same-test-id",
    "phase-cascade",
    "cosmetic-cluster",
    "regression-marker"
    /* "same-owner" omitted — disabled for this repo */
  ]
}
```

If `enabledHeuristics` is absent, all heuristics are enabled. Add or
remove names freely; unknown names are ignored.

## Adding a new heuristic

Copy a row from the catalog above into this file. Give the heuristic a
name (kebab-case), describe the signal in 1–2 sentences, describe what
text to cite, and pick a proposed action from the existing set or add a
new one with a confirmed-action contract entry.

The agent applies the new row on the next session — no other changes
required. See [extending-the-skill.md](extending-the-skill.md).

## Anti-patterns

| Don't | Why |
|-------|-----|
| Auto-merge without user confirm | The skill's value is the explainable suggestion, not the action |
| Suggest a confidence score | Heuristics are binary by design — either the signal fires or it doesn't |
| Use embeddings or an external LLM | Adds a dep, hides reasoning, and isn't repeatable across sessions |
| Cite "looks similar" without a text quote | Every suggestion must cite the matching text |
| Re-surface a rejected suggestion next session | Check Triage logs for prior rejections |
| Run heuristics inside another heuristic ("if A fires, also check B") | Keep heuristics independent; combine in presentation, not in code |
