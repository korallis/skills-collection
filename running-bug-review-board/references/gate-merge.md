# Gate merge + sign-off

Final step of every QA pass. Even a sequential solo run produces a merge
doc — it's the single source of truth for "Phase N ready? YES/NO".

## Contents

- Inputs
- Outputs
- Gate update rule
- Verdict logic
- Merge doc top block (mandatory)
- Verdict
- Cross-link everywhere
- Shard summary table
- After verdict
- Handoff prompt — what makes it good
- Commit hygiene
- Definition of done for this step

## Inputs

- Every `docs/qa/runs/QA-<shard>-run-YYYY-MM-DD.md` from the pass
- Your own coordinator verification of critical paths
- Open bugs in `docs/qa/bug-reports/BUG-*.md` (status `open` or `fixed`)
- Prior merge doc (for context on what was already verified)

## Outputs

1. **`docs/qa/runs/COORDINATOR-MERGE-YYYY-MM-DD.md`** — see
   [templates/coordinator-merge.md](templates/coordinator-merge.md)
2. **`docs/QA_GATES.md`** (or your repo's equivalent) — Gate NN boxes
   updated (☑ on confirmed PASS, ☐ on FAIL or BLOCKED)
3. **`docs/qa/bug-reports/README.md`** — index table rows added /
   updated
4. **Phase doc** — § QA status block updated with date + link
5. (If YES verdict) **`docs/CURRENT_STATE.md`** + **`docs/README.md`**
   phase tables updated

Adapt paths to whatever the target repo uses.

## Gate update rule

A Gate item flips to ☑ only when:

- ≥ 1 Test ID mapped to that gate **passed** with evidence
- No related bug is still `open` against the same gate
- The test was run on the current `main` (or the branch under sign-off),
  not an older build

If a gate has no test coverage at all, **do not** mark it ☑. Add a
`TODO` row to the manual test plan instead.

## Verdict logic

| Phase status | Verdict |
|--------------|---------|
| All Test IDs PASS + Gate all ☑ + zero open P0/P1 | **YES** |
| Any open P0 against the phase | **NO** |
| Any open P1 against the phase | **NO** |
| Some Test IDs BLOCKED (infra only, no product bug) | **NO** (run sequential wrap-up to clear) |
| Out-of-scope items still ☐ in the gate | Allowed — note in phase doc § Known issues |

Be honest. Incomplete coverage ≠ pass. The 2026-05-19 Mokuhoe run
correctly resisted a YES despite no confirmed product bugs because three
shards stalled.

## Merge doc top block (mandatory)

Even before the results tables, lead with:

```markdown
## Verdict

**Phase N ready?** YES / NO

### Open P0
- BUG-XXX – title

### Open P1
- BUG-YYY – title
- (also list remaining unrun Test IDs as P1 follow-ups)

### Handoff prompt (paste into a fresh agent if NO)

(One paragraph the next QA agent can copy without reading the rest.)
```

This lets the user (and any future agent) get the answer in 5 seconds.

## Cross-link everywhere

Each artifact updated in this step must link back to the merge:

- `docs/QA_GATES.md` top: "Last QA merge: YYYY-MM-DD — link"
- Phase doc § QA status: "Sign-off: YES/NO (YYYY-MM-DD) — link"
- `docs/qa/bug-reports/README.md`: add a "<date> coordinator notes"
  subsection summarizing pass-level follow-ups (not new bugs)

## Shard summary table

```markdown
| Shard | Scenarios | Status | Report |
|-------|-----------|--------|--------|
| QA-A | P{N}-A* | Complete / Partial / Stalled | [link] |
```

Followed by:

- Critical paths the coordinator personally re-verified (with evidence)
- Regression matrix table (PASS / FAIL / Not run)
- Bugs filed in this pass
- Process notes (auth rate-limit, browser contention) — non-product
  issues for the next coordinator

## After verdict

| Verdict | Next |
|---------|------|
| YES | Update CURRENT_STATE, README; commit "Phase N QA sign-off (YYYY-MM-DD)"; phase agent can start next phase |
| NO | Trigger [sequential-wrapup.md](sequential-wrapup.md) with the handoff prompt; loop until YES |

## Handoff prompt — what makes it good

The handoff prompt at the top of the merge doc must let a fresh agent
start without reading anything else. Include:

- Branch / commit they should test
- Open bugs they're verifying or working around
- Test IDs left to run (with Gate IDs)
- Test data already provisioned (group ID, invite URL, admin email,
  passwords reference)
- Known infra gotchas for this repo

Example (paste-ready):

```
You are the **sequential QA wrap-up agent** for ${PROJECT} Phase ${N} on
branch ${BRANCH}. Read .agents/skills/running-bug-review-board/SKILL.md
and apply references/sequential-wrapup.md. Open bugs: ${BUG-IDS}.
Remaining Test IDs: ${IDs}. Test data: group ${ID}, invite ${URL},
admin ${EMAIL} / vault, OTP ${FIXTURE}. Verdict goes back into this
merge doc.
```

## Commit hygiene

```bash
git add docs/qa docs/QA_GATES.md docs/phases/phase-NN-*.md docs/CURRENT_STATE.md
git commit -m "QA Phase N — sign-off YES (YYYY-MM-DD)"
# or
git commit -m "QA Phase N — sign-off NO; open BUGs and handoff in merge doc"
```

Never amend a prior phase's commits with new QA data — append.

## Definition of done for this step

- [ ] Verdict line at top of merge doc (YES or NO)
- [ ] Open P0/P1 list (or "None")
- [ ] Handoff prompt (only when NO)
- [ ] Gate boxes updated
- [ ] Bug index updated
- [ ] Phase doc § QA status updated
- [ ] Cross-links from gates / phase doc → merge doc
- [ ] (If YES) CURRENT_STATE / README updated
- [ ] Committed with correct message

If any box is unchecked, the merge isn't done — and the next agent will
have to redo this work.
