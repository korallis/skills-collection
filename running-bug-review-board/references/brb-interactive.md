# Interactive Bug Review Board (BRB)

The auto QA pass finds and files bugs. The interactive BRB **triages**
those bugs **with the user in the loop**. It is a meeting the agent
runs, not an automation.

The two workflows are intentionally separate — running them in the same
session lets triage bias contaminate the auto pass and lets auto-pass
findings flood the BRB agenda. Use the auto pass to discover; use the
BRB to decide.

## Contents

- When to run a BRB
- Inputs
- Workflow
- Rules
- Cross-bug observations
- Anti-patterns
- Outputs
- Definition of done

## When to run a BRB

- Weekly cadence (or pre-sign-off) — clear the backlog of `open` /
  `in-progress` bugs.
- After engineering ships fixes — verify `fixed` bugs and flip them to
  `verified`.
- When the team needs to triage priorities ahead of a release.
- Whenever the user says "let's run a BRB", "triage these bugs",
  "review what's open", or similar.

Use a **different agent / session** from the auto pass. The facilitator
agent's prompt is at
[templates/brb-interactive-prompt.md](templates/brb-interactive-prompt.md).

## Inputs

- `docs/qa/qa-config.json` — tracker config + heuristics config
- `docs/qa/bug-reports/` — every bug (all statuses)
- `docs/qa/runs/COORDINATOR-MERGE-*.md` — latest verdict
- `docs/qa/report/index.html` — current dashboard (regenerate if stale)
- The user, present in the chat

## Workflow

### Step 1 — Pre-BRB pull

Before opening the agenda, run the bi-directional **pull** per
[issue-trackers.md](issue-trackers.md). This catches engineering's
work that's already flowed through the tracker so the meeting doesn't
re-decide things.

The pull may surface user-decision diffs (status divergence,
re-prioritization, untracked-locally bugs). Resolve those first as a
short preamble:

```
Before we start: pull found 3 items that need your call.
  • BUG-019: tracker says P0, local says P1. Which?
  • BUG-014: tracker marked verified; local says in-progress. Confirm?
  • LIN-3344: exists in Linear but not locally. Import? Ignore? (config
    says "ask".)
```

### Step 2 — Refresh the HTML report

If `docs/qa/report/index.html` is older than the latest bug or run
markdown, regenerate per
[html-report-style-guide.md](html-report-style-guide.md). The user will
want to share the dashboard during the session.

### Step 3 — Run the triage heuristics

Apply [triage-heuristics.md](triage-heuristics.md) across the open /
in-progress / fixed bugs. Render a single **Suggestions** card grouped
by proposed action (merge, link, consolidate, defer). The user confirms
or rejects each suggestion.

This step is the BRB's killer feature: it's much faster to triage a
clustered backlog than a flat list, and the heuristics-as-named-text
keeps the agent honest.

### Step 4 — Per-bug triage

Walk the remaining open / in-progress / fixed bugs that the Suggestions
card didn't already resolve. For each bug, present a compact card and
ask the user a tight checklist:

```
BUG-027 — "Sign-in lands on /dashboard instead of /groups/[id]"
  Priority: P1 (was P1 last BRB)
  Status:   in-progress (assigned @engineer)
  Reported: 2026-05-22 by qa-agent
  Evidence: 2 screenshots, 1 console error, server row attached
  Linear:   LIN-1244

  Confirm priority?     P0  P1  P2  defer  wontfix
  Status update?        in-progress → fixed | verified | reopen | duplicate
  Owner change?         (current: @engineer)
  Link a PR?            paste URL
  Notes for triage log? free text
```

Wait for the user. Apply the answers. Move on.

### Step 5 — Re-test fixed bugs

For every bug marked `fixed` (either by the tracker pull or in this
session), re-test the linked Test ID. Two options:

- **In-place** if the facilitator agent has browser MCP access. Run
  the scenario, capture evidence, flip to `verified` on PASS or
  reopen on FAIL.
- **Delegate** to a sequential QA sub-agent using the prompt in
  [templates/sequential-prompt.md](templates/sequential-prompt.md),
  scoped to that bug's Test ID. Wait for the sub-agent to return.

Either way, the result feeds back into the agenda — `verified` bugs
get a final Triage log entry; reopened bugs go back to the per-bug
queue.

### Step 6 — Sync to tracker

For every status change made this session, push to the tracker per
[issue-trackers.md](issue-trackers.md). Update labels, link PRs in
comments, write a `BRB: <date>` comment summarizing the decision.

If the same agent doesn't have tracker access, hand off a paste-ready
list of MCP tool calls / `gh` commands to the user.

### Step 7 — Regenerate HTML

After all updates, regenerate the dashboard + per-bug pages per
[html-report-style-guide.md](html-report-style-guide.md). The version
marker stays `<!-- skill:running-bug-review-board v0.2 -->`.

### Step 8 — Write BRB minutes

Save to `docs/qa/runs/BRB-YYYY-MM-DD.md` using
[templates/brb-minutes.md](templates/brb-minutes.md). The minutes are
the durable record of *why* each decision was made.

### Step 9 — Hand off

If new findings during the BRB warrant a fresh QA pass (e.g. a re-test
revealed a different regression), surface them but **do not file new
bugs in the BRB session**. Recommend the user start a separate auto
pass per [parallel-coordinator.md](parallel-coordinator.md) or
[sequential-wrapup.md](sequential-wrapup.md).

## Rules

| Rule | Why |
|------|-----|
| The agent **asks**; the user **decides** | Triage is a judgment call; the agent's job is to organize information and apply confirmed decisions |
| **No new bugs filed during BRB** | Cross-contamination — file in a separate auto pass and keep attribution clean |
| Update markdown **and** tracker for every change | Drift between the two is the most expensive failure mode |
| **No auto-merge** from heuristic suggestions | Every merge / dedup needs user confirm; see [triage-heuristics.md](triage-heuristics.md) |
| Never re-prioritize unilaterally | Priority is a real conversation; always confirm |
| Always run the pre-BRB pull | Without it, you might re-decide something engineering already resolved |
| Always regenerate HTML at the end | The dashboard is what stakeholders see |
| BRB and auto pass run in **separate sessions** | Keeps triage bias out of the auto pass |

## Cross-bug observations

Toward the end of the session (after per-bug triage, before the minutes),
look for patterns the heuristics didn't catch:

- Recurring component / file across multiple unrelated bugs
- Recurring persona experiencing different bugs
- A particular phase doc that keeps producing regressions
- An engineering pattern (e.g. "every bug touches optimistic UI")

Record these in the minutes' **Cross-bug observations** section.

## Anti-patterns

| Don't | Why |
|-------|-----|
| Run BRB and an auto pass in the same chat | Bias and attribution chaos |
| Skip the pre-BRB pull to "save time" | Wastes more time deciding things already resolved |
| File new bugs during BRB | Use a separate auto pass |
| Mark a `fixed` bug `verified` without re-testing | Untested verifications come back as regressions |
| Edit a bug's markdown without updating the tracker (or vice versa) | Drift between sources is the worst failure mode |
| Re-surface a previously-rejected heuristic suggestion | Check Triage logs for prior rejections |
| Skip writing minutes because "we'll remember" | The minutes are the artifact stakeholders read |

## Outputs

| Path | What |
|------|------|
| Updated `docs/qa/bug-reports/BUG-NNN-*.md` | Status / priority / triage log / tracker IDs |
| New `docs/qa/runs/BRB-YYYY-MM-DD.md` | Session minutes |
| Updated `docs/qa/report/index.html` and detail pages | Refreshed dashboard |
| Tracker-side updates | Per the chosen tracker's adapter |
| Final chat message | One-paragraph summary + minutes link |

## Definition of done

- [ ] Pre-BRB pull ran; surfaced diffs resolved
- [ ] Heuristics ran; Suggestions card confirmed/rejected by user
- [ ] Per-bug triage completed
- [ ] `fixed` bugs re-tested and flipped to `verified` or reopened
- [ ] Tracker pushed/updated for every change
- [ ] HTML regenerated
- [ ] BRB minutes written
- [ ] Committed with message like `BRB <date> — triaged N bugs`
