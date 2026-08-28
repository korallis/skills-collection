# BRB session — {YYYY-MM-DD}

| Field | Value |
|-------|--------|
| **Facilitator** | {Agent or human name} |
| **Attendees** | {User + others present} |
| **Phase scope** | {Phase N or "all open"} |
| **Latest merge** | [link to COORDINATOR-MERGE-{DATE}.md](COORDINATOR-MERGE-{DATE}.md) |
| **HTML report** | [link to ../report/index.html](../report/index.html) |
| **Tracker pulled** | {linear / github / jira / none} at {ISO timestamp} |

---

## Contents

- Pre-BRB pull summary
- Suggestions disposition
- Decisions
- Re-tests this session
- Cross-bug observations
- Tracker sync
- Action items
- Recommended follow-up auto QA pass
- Related

## Pre-BRB pull summary

| Metric | Count |
|--------|------:|
| Bugs pulled | N |
| Status updates | N |
| Comment additions | N |
| PR links added | N |
| Divergences surfaced | N |
| Untracked-locally | N |

### Divergences resolved before agenda

- **BUG-XXX** — tracker says {X}, local said {Y}. Decided: {decision} by {user}.
- ...

---

## Suggestions disposition

Heuristic-driven suggestions surfaced this session. Source:
[triage-heuristics.md](../../.agents/skills/running-bug-review-board/references/triage-heuristics.md).

| Cluster | Heuristics | Proposed | Disposition | Decided by |
|---------|-----------|----------|-------------|-----------|
| BUG-012 → BUG-007 | same-suspect-file, steps-prefix-overlap, same-console-error | Merge as duplicate | Accepted | {user} |
| BUG-014 ↔ BUG-007 | same-persona-surface-outcome | Link as related | Accepted | {user} |
| BUG-021, BUG-022, BUG-024 | cosmetic-cluster | Consolidate into new BUG-025 | Rejected — different surfaces on re-read | {user} |

---

## Decisions

| Bug | Was | Now | Owner | Notes |
|-----|-----|-----|-------|-------|
| BUG-001 | open / P0 | fixed / P0 | @engineer | PR #42 merged {DATE} |
| BUG-005 | open / P1 | deferred / P2 | — | Move to Phase 3 polish |
| BUG-007 | open / P0 | verified / P0 | @engineer | Re-tested by sequential agent on commit abc1234 |
| BUG-012 | open / P1 | duplicate / — | — | Duplicate of BUG-007 |

---

## Re-tests this session

| Bug | Test ID | Result | Evidence |
|-----|---------|--------|----------|
| BUG-001 | P2-C3 | PASS → verified | {sub-agent run report link} |
| BUG-019 | P2-D2 | FAIL → reopen | {evidence link} |

---

## Cross-bug observations

- {Pattern noticed by facilitator across multiple bugs}
- {e.g. "Multiple P1s touch convex/invites.ts — engineering should
   audit the file."}

---

## Tracker sync

| Tracker | Pushed (new) | Updated | Pulled | Diverged |
|---------|-------------:|--------:|-------:|---------:|
| {tracker} | N | N | N | N |

---

## Action items

| Owner | Action | When |
|-------|--------|------|
| {who} | {what} | {when} |

---

## Recommended follow-up auto QA pass

If any regression / re-test failure warrants a fresh pass, paste-ready
handoff prompt below. **Do not** start the pass from this BRB session.

> You are the **sequential QA wrap-up agent** for {PROJECT} Phase {N}.
> Read ~/.agents/skills/running-bug-review-board/SKILL.md and apply
> references/sequential-wrapup.md. Open bugs: {LIST}. Remaining Test IDs:
> {LIST}. Test data: …

---

## Related

- [Latest merge](COORDINATOR-MERGE-{DATE}.md)
- [Bug reports](../bug-reports/README.md)
- [HTML dashboard](../report/index.html)
- [Skill SKILL.md](~/.agents/skills/running-bug-review-board/SKILL.md)
