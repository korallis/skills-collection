# Workflow — PM + QA + Engineer trifecta

The full decision tree for any QA pass. SKILL.md gives the shape; this gives
the *how*. Read top-to-bottom on first pass; jump to the numbered sections
on later passes.

## Contents

- 1. Scope the pass
- 2. Discover the app
- 3. Generate the test plan if missing
- 4. Validate the environment
- 5. Choose mode
- 6. Execute
- 7. Look for invalidated assumptions (engineering hat)
- 8. File bugs
- 9. Merge and sign off
- 10. Hand off to next pass
- 11. Schedule interactive BRB
- Anti-patterns
- Decision flowchart
- When a QA pass reveals work bigger than QA

## 1. Scope the pass

Ask yourself (or the user, if ambiguous):

- Which **phase / sprint / build** are we QAing?
- Is this a **fresh first pass**, a **wrap-up** of a partial run, or a
  **bug re-test** after engineering shipped fixes?
- Are there **upstream phases / dependencies not yet QAed**? If yes — flag
  it. QA in dependency order; later phases assume earlier gates pass.

Find the artifacts (paths vary by repo — adapt):

```bash
ls docs/phases/phase-${NN}-*.md          # or sprints/, milestones/, etc.
ls docs/qa/phase-${NN}-*-manual-test-plan.md
grep -n "Gate ${NN}" docs/QA_GATES.md    # or CHECKLIST, RELEASE_GATES
ls docs/qa/runs/                          # prior pass evidence
ls docs/qa/bug-reports/BUG-*.md           # open bugs to re-test
```

If none of these exist, scaffold them with `scripts/scaffold-qa.sh` and
generate the test plan via [test-plan.md](test-plan.md).

## 2. Discover the app

Read [discovering-the-app.md](discovering-the-app.md). Key inputs:

1. **Product spec / README / landing page** — what the app **promises**
2. **Phase or sprint doc** — what was just built; **Known issues /
   deferrals** drive scope
3. **QA gates / checklist** — minimum bar
4. **Architecture / agent handoff doc** (if it exists) — non-negotiable
   patterns; deviations are bugs
5. **Latest coordinator merge** — what's already verified or blocked
6. **Open bug reports** — re-test these before new scenarios

Take notes on:
- **Assumptions to invalidate** — phase doc says "should" do X but maybe
  no longer holds (schema changed, dependency upgraded, component renamed)
- **Out-of-scope items** — record but never fail a phase on these
- **Personas needed** — admin / member / new user / non-member / etc.

## 3. Generate the test plan if missing

For phases without a plan, generate one **before** testing. See
[test-plan.md](test-plan.md). The plan is the contract between
engineering, QA, and product.

## 4. Validate the environment

Run the project's validation pipeline (varies by stack):

```bash
# Examples — use whichever the project documents
bun run validate
npm run typecheck && npm run build
pnpm test:ci
make lint test
```

Failure here is a **blocker**, not a bug. Do not start scenarios until the
build passes.

Spot-check the dev environment:

- Backend / database / API up
- Auth provider keys configured
- Browser viewport set to the device mode under test (cover mobile / tablet / desktop)

## 5. Choose mode

| Signal | Mode |
|--------|------|
| Full pass, time available, multi-agent OK | **Parallel coordinator** — [parallel-coordinator.md](parallel-coordinator.md) |
| Full pass and the `waves` / `waves-codex` skill is installed | **Parallel coordinator run as a bounded wave** — [parallel-coordinator.md § Run the pass as a wave](parallel-coordinator.md) |
| Prior parallel run partial; <½ shards remain | **Sequential wrap-up** — [sequential-wrapup.md](sequential-wrapup.md) |
| Re-testing 1–3 fixed bugs | Sequential, scoped to those Test IDs |
| Phase code clearly not implemented yet | Stop. Tell user the phase needs engineering first |
| Phase doc unclear on user-visible behavior | Read product spec; write a hypothesis; ask user before testing |

## 6. Execute

Per scenario:

1. Reach the start state (incognito-equivalent if "fresh user").
2. Take a fresh page snapshot **before each interaction** (refs go stale
   after navigation/click).
3. Capture evidence — snapshot, screenshot when visually meaningful,
   console errors, server data row.
4. Mark **PASS / FAIL / BLOCKED**. Note linked **Gate item** ID where one
   exists.
5. On **FAIL** — file `BUG-NNN-*.md` immediately ([bug-filing.md](bug-filing.md)).
6. On **BLOCKED** — note why (env, auth rate-limit, missing persona) and
   continue with scenarios that don't depend on the broken flow.

Keep a running results table; do not wait until the end to write it down.
The cost of losing partial results to a crash or context switch is high.

## 7. Look for invalidated assumptions (engineering hat)

Even on PASS, flag in run report notes when:

- Component or file path mentioned in phase doc no longer exists
- Function / API signature changed (extra args, new return shape)
- New client orchestration appeared in a flow the docs say is server-driven
- UI fields visible to the user not described in the phase doc
- Mobile readability issues (overflow, tiny tap targets, low contrast)
- Console warnings that weren't there before
- Performance regressions (page load > spec target, hangs, layout thrash)

These belong in **Recommended engineering priority** in the run report.
Even if functional, they are technical debt or upcoming bugs.

## 8. File bugs

See [bug-filing.md](bug-filing.md). Every FAIL becomes a `BUG-NNN-*.md`.
P0 stops the phase; P1 blocks sign-off; P2 defers.

The bug report is what engineering acts on. Empty steps = wasted bug = no
fix = same bug next pass.

## 9. Merge and sign off

See [gate-merge.md](gate-merge.md). The coordinator merge doc is the
**single source of truth** for "Phase N ready? YES/NO".

Even a sequential solo pass produces a merge doc. The verdict line at the
top (≤2 lines) is what stakeholders read first.

## 10. Hand off to next pass

If verdict is NO, write a copy-paste handoff prompt at the top of the
merge doc covering:

- Open P0/P1 bugs (with bug IDs)
- Remaining Test IDs (with Gate items)
- Persona accounts and test data already provisioned (group ID, invite
  URL, admin credentials, etc.)
- Known infra gotchas (auth rate-limit, browser session hygiene)

This is what makes runs **recoverable** — the next agent should not have
to rediscover state.

## 11. Schedule interactive BRB

The auto pass discovers bugs. The Bug Review Board **triages** them with
the user in the loop. Use a **separate session** — running BRB inside an
auto pass lets triage bias contaminate the pass and confuses attribution.

When to schedule BRB:
- After a NO verdict: triage the open P0 / P1 before the next pass.
- After a YES verdict: usually only needs to verify P2 deferrals and
  ack any post-merge tracker pulls.
- On a regular cadence (weekly, pre-release) regardless of verdict.

See [brb-interactive.md](brb-interactive.md). The facilitator prompt
lives at
[templates/brb-interactive-prompt.md](templates/brb-interactive-prompt.md).

## Anti-patterns

| Don't | Why |
|-------|-----|
| Mark scenarios PASS from code inspection alone | The user doesn't experience source; they experience the app |
| Defer P0 bugs to "next phase" | Foundation bugs cascade everywhere |
| Trust prior PASS marks without re-running on a fresh build | Regressions appear from unrelated phase work |
| Run multiple QA agents on one browser tab | Confirmed auth-provider session loss across multiple runs |
| Edit phase doc to match buggy behavior | Hides the regression; file a bug instead |
| File a bug without **Steps to reproduce** | Engineering can't act on it |
| Stop QA early because "this looks fine" | Looking fine ≠ verified |
| Run only the happy path | The happy path is what engineers tested already |

## Decision flowchart

```
Build healthy?  ──no──→ STOP. Tell user. Do not file build issues as bugs.
     │ yes
     ▼
Plan exists?    ──no──→ Generate plan → return here.
     │ yes
     ▼
Open P0/P1?     ──yes─→ Re-test those FIRST (Block A in sequential).
     │ no
     ▼
Multi-agent OK? ──no──→ Sequential mode top-to-bottom.
     │ yes
     ▼
Time / fresh build → Parallel coordinator → write-path shard first.
     │
     ▼
Run scenarios → file bugs → merge → verdict → hand off if NO.
```

## When a QA pass reveals work bigger than QA

Stop testing if you find:

- A **missing feature** the phase claims exists (no code path at all)
- A schema diverging from the spec across multiple scenarios
- A P0 bug blocking every remaining scenario
- Auth provider throttling for >5 minutes (env, not product)

Surface the finding. The user decides whether to escalate to engineering
or carve a smaller phase. Continuing wastes time on a foundation that
needs replacing.
