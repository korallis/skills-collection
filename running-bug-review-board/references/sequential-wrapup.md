# Sequential wrap-up mode

Use when a prior parallel run stalled, or for any pass small enough to
run end-to-end in one session. **One agent, one browser tab, one
scenario at a time.** This mode is the most reliable.

## Contents

- When to use
- Why sequential is preferred for cleanup
- Pre-flight
- Build a checklist (Blocks A–D pattern)
- Session hygiene (required)
- Tail-tracking
- When to escalate
- Block A — pull before re-testing
- Verdict
- Sequential agent prompt
- Anti-patterns
- Mid-pass discoveries
- Time budget

## When to use

- A previous coordinator merge says "Phase N ready? NO" with remaining
  scenarios
- Engineering shipped fixes for open P0/P1 bugs — re-test those Test IDs
- Solo QA run on a small phase
- Browser tool can't isolate per-agent

## Why sequential is preferred for cleanup

Real-run evidence: parallel auth signups throttle, and the IDE browser
tab is shared by default. Sequential avoids both: no rate-limit storm,
no session bleed, no "no sign in attempt" loops.

## Pre-flight

```bash
# Adapt to your repo's commands
bun run validate    # build / typecheck must pass
bun dev             # http://localhost:3000
```

Read these in order:

1. Latest `docs/qa/runs/COORDINATOR-MERGE-*.md` — what's remaining
2. `docs/qa/bug-reports/BUG-*.md` with status `open` or `fixed` (re-test
   first)
3. The phase manual test plan
4. The phase doc § Known issues / deferrals
5. `docs/QA_GATES.md` Gate NN

## Build a checklist (Blocks A–D pattern)

| Block | Purpose | Order |
|-------|---------|-------|
| **A. Bug re-tests** | Verify `fixed` bugs; reopen if regressed | 1st |
| **B. Gate gaps** | Run scenarios that were BLOCKED or skipped | 2nd |
| **C. Critical paths** | Re-run highest-risk Test IDs on the fixed build | 3rd |
| **D. Close-out** | Update gates, bug index, phase doc, write verdict | last |

Write the checklist into a fresh
`docs/qa/runs/QA-SEQUENTIAL-run-YYYY-MM-DD.md` before testing. Each row
gets a result.

## Session hygiene (required)

See [session-hygiene.md](session-hygiene.md) for the full rules.
Per-scenario:

1. If next scenario is **fresh user** or **no context**: clear stale
   storage (`sessionStorage.clear(); localStorage.clear()`), or use a
   fresh tab.
2. If previous scenario hit **"Too many requests"**: wait 30 seconds
   before next signup.
3. New `+runMMDD-N` suffix per fresh account.
4. Browser flow: `navigate → lock → snapshot → interact → unlock`
   (unlock only when fully done with the tab).

## Tail-tracking

Keep your scratch results table updated **as you go**, not at the end.
The cost of losing partial results to a crash is high.

## When to escalate

Stop sequential and ask the user when:

- A scenario reveals a missing **feature** (not bug) — phase doc claims
  it exists but no code path does
- DB / schema diverges from the phase doc in a way that affects multiple
  scenarios
- A P0 bug blocks every remaining scenario
- Auth provider is throttling for >5 minutes

## Block A — pull before re-testing

Before re-testing any `fixed` or `in-progress` bug in Block A, run a
**pull** from the configured tracker per
[issue-trackers.md](issue-trackers.md). Engineering may already have
flipped the status to `verified`, or commented with reproduction notes
worth reading before you spend cycles re-testing.

```bash
bash ~/.agents/skills/running-bug-review-board/scripts/bugs-needing-pull.sh "$REPO_ROOT"
```

Apply the pull's reconciliation rules; surface any divergence to the
user before continuing.

## Verdict

Write the final verdict in the coordinator merge doc, even if you ran
solo. Same template as parallel ([gate-merge.md](gate-merge.md)). If
verdict is YES, also:

- Update `docs/CURRENT_STATE.md` (or your repo's status doc): move phase
  items from Remaining → Done
- Update `docs/README.md` phase table status
- Update phase doc § QA status with "Sign-off: YES (YYYY-MM-DD)" + link
  to merge

**Regenerate the HTML report** per
[html-report-style-guide.md](html-report-style-guide.md) before
committing the merge. If a tracker is configured, also run
`scripts/bugs-needing-sync.sh` and push any new bugs filed during the
wrap-up.

## Sequential agent prompt

Use [templates/sequential-prompt.md](templates/sequential-prompt.md).
Fill in:

- `{PHASE_NUM}`
- `{OPEN_BUG_IDS}`
- `{REMAINING_TEST_IDS}`
- `{SHARED_ARTIFACTS}` (group ID, invite URL, admin creds, existing
  personas)
- `{RUN_DATE}`

## Anti-patterns

| Don't | Why |
|-------|-----|
| Skip Block A (bug re-tests) | If a fix didn't actually fix, you'll waste the rest of the pass on the same bug |
| Mark a scenario PASS when "it didn't crash" | Crash-free ≠ correct user experience |
| Move to Block B before Block A is fully verified | Cascading bugs hide behind half-fixed ones |
| Write the verdict before D1 is complete | Half-merged docs confuse the next pass |
| Spawn child browser sub-agents in sequential mode | Defeats the whole purpose |

## Mid-pass discoveries

If during sequential you find a regression in a previously-PASSed
scenario, **don't ignore it**:

1. Add a row to your run report: `<old Test ID> | RE-FAIL | <bug ID>`
2. File a new bug or reopen the original
3. Continue with the original block — but flag the regression in the
   merge doc's "Process notes" so the next run starts there

## Time budget

A solo sequential pass on a typical phase (15–25 scenarios) takes
60–120 minutes including bug filing. Budget conservatively. If you blow
the budget on a single block, surface it — the user may want to split.
