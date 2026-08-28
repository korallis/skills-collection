# QA Coordinator Merge — Phase {N} — {YYYY-MM-DD}

## Contents

- Verdict
- Run setup
- Shard completion
- Critical paths (coordinator-verified)
- Regression matrix
- Bugs filed this pass
- Tracker sync (this pass)
- Generated artifacts
- Sign-off criteria
- Recommended next steps
- Process notes
- Related

## Verdict

**Phase {N} ready?** YES / NO

### Open P0
- {BUG-NNN — title} *(or "None")*

### Open P1
- {BUG-NNN — title} *(or "None")*
- {Remaining unrun Test IDs as P1 follow-ups}

### Handoff prompt (if NO — paste into a fresh agent)

> You are the **sequential QA wrap-up agent** for {PROJECT} Phase {N} on
> branch {BRANCH}. Read `.agents/skills/running-bug-review-board/SKILL.md`
> (or `~/.agents/skills/running-bug-review-board/SKILL.md`) and apply
> [sequential-wrapup.md](../../../.agents/skills/running-bug-review-board/references/sequential-wrapup.md).
> Open bugs: {BUG IDs}. Remaining Test IDs: {list}. Test data: group/org
> `{ID}`, invite/share `{URL}`, admin `{email}` / vault, OTP/fixture
> `{FIXTURE}`. Verdict goes back into this merge doc.

---

## Run setup

| Check | Status |
|-------|--------|
| `<validate command>` | PASS / FAIL |
| `<dev command>` @ localhost:3000 | Running / Not running |
| Write-path shard ran first | Yes / No |
| Parallel shards launched | {list} |
| Sequential follow-ups | {list} |

### Shared test artifacts

| Key | Value |
|-----|--------|
| Group / org / tenant ID | `{id}` |
| Group / org name | {…} |
| Primary invite / share URL | `{URL}` |
| Admin | `{email}` / vault |
| OTP / verification fixture | `{FIXTURE}` |
| Sign-up flow | {short recipe} |
| Sign-in flow | {short recipe} |

## Shard completion

| Shard | Scenarios | Status | Report |
|-------|-----------|--------|--------|
| QA-A | … | Complete / Stalled | [link] |
| QA-B | … | … | [link] |
| QA-C | … | … | [link] |
| QA-D | … | … | [link] |
| QA-E | … | … | [link] |
| QA-F | … | … | [link] |

## Critical paths (coordinator-verified)

| Path | Result | Evidence |
|------|--------|----------|
| {Highest-risk Test ID} | PASS / FAIL | {snapshot summary, server row, URL} |

## Regression matrix

| Row | Result | Notes |
|-----|--------|-------|
| New user + invite | PASS / FAIL / Not run | |
| New user no invite | … | |
| Onboarded + invite claim | … | |
| Already member + invite | … | |
| Bad code on dashboard | … | |
| Revoked code | … | |

## Bugs filed this pass

| Bug | Title | Priority | Status |
|-----|-------|----------|--------|
| BUG-NNN | … | P0/P1/P2 | open |

## Tracker sync (this pass)

| Tracker | Pushed (new) | Updated | Pulled | Diverged |
|---------|-------------:|--------:|-------:|---------:|
| {linear/github/jira/notion/none} | N | N | N | N |

*See [issue-trackers.md](../../.agents/skills/running-bug-review-board/references/issue-trackers.md) for the bi-directional sync workflow.*

## Generated artifacts

| Artifact | Path |
|----------|------|
| HTML dashboard | `docs/qa/report/index.html` |
| Per-bug pages  | `docs/qa/report/bugs/BUG-*.html` |
| Per-run pages  | `docs/qa/report/runs/*.html` |
| Stylesheet     | `docs/qa/report/assets.css` |

## Sign-off criteria

| Criterion | Met? |
|-----------|------|
| All P{N}-* scenarios executed | Yes / No |
| Regression matrix green | Yes / No / N/A |
| Gate {N} all pass | Yes / No |
| No open P0/P1 bugs | Yes / No |

## Recommended next steps

1. {action — re-run X, fix bug Y, etc.}
2. …

## Process notes

- {auth rate-limit / browser contention / backend MCP timeouts}
- Suggestions for the next pass

---

## Related

- [Manual test plan](../phase-{NN}-{slug}-manual-test-plan.md)
- [QA Gates](../../QA_GATES.md)
- [Phase {N} doc](../../phases/phase-{NN}-{slug}.md)
- [Skill SKILL.md](~/.agents/skills/running-bug-review-board/SKILL.md)
