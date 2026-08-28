# Parallel coordinator mode

Use when running a fresh full pass with multiple QA agents. Lessons from
real runs are baked in: **the write-path shard runs first** to seed
shared test data, and shards do not share a browser tab.

## Contents

- When to use
- When NOT to use
- Pre-flight (coordinator only)
- Shard map (generalize per phase)
- Write-path-first rule
- Launching shards
- Run the pass as a wave (when `waves` / `waves-codex` is installed)
- While shards run
- Hand off if shards stall
- Merge
- Common pitfalls (observed)
- Shard prompt
- Coordinator self-check before merging

## When to use

- Phase is freshly implemented and needs a full pass
- Multiple agents / sessions available
- Time-boxed (parallel is faster but introduces auth / browser
  contention)

## When NOT to use

- Only 1–3 bug retests pending → use [sequential-wrapup.md](sequential-wrapup.md)
- One agent only → run scenarios top-to-bottom; do not pretend to shard
- Browser tool can't isolate per-agent (shared tab) → use sequential

## Pre-flight (coordinator only)

```bash
# Adapt these to your repo's commands
bun run validate        # build / typecheck must pass
bun dev                 # leave running
git status              # clean or known-state
```

Confirm:
- Auth provider dev keys are active
- Backend / DB available
- Prior coordinator merge in `docs/qa/runs/` so you don't overwrite

## Shard map (generalize per phase)

Generate the shard map from your test plan. Default skeleton:

| Letter | Block intent | Personas needed |
|--------|-------------|-----------------|
| A | Public + happy path (no auth or fresh signup only) | Fresh user |
| B | Returning user / persistence | 1 onboarded user |
| C | **Admin write paths** — runs first, seeds shared state | Admin |
| D | New user via shared write-path output (e.g. invite) | Admin + 2 fresh users |
| E | Returning user via shared write-path output | Admin + 2 onboarded users |
| F | Roles / access control / negative tests | Admin + member + co-admin |

Keep shards **non-overlapping**. If two shards would touch the same
record, merge them or split by persona.

**Coverage gate (before launching anything).** Enumerate every Test ID in
the phase manual test plan (per platform block for monorepos) and assign
each to exactly one shard letter. Assert the partition: every scenario in
exactly one shard, shard counts sum to the plan total, zero duplicates. A
scenario that lands in no shard is a silent blind spot the merge will
never catch; print the per-shard counts in the coordinator notes so the
merge can check them off.

## Write-path-first rule

The write-path shard (often "C") creates the artifact every other shard
depends on (a group, an org, a workspace, an invite). Run it before
launching the rest.

After the write-path shard reports completion, copy these into the other
agents' prompts:

- IDs created (group / org / tenant / project ID)
- Invite URLs / share codes
- Admin email + reference to where the password is stored
- Backend deployment URL (so subagents can verify data via MCP if
  available)
- Sign-up + sign-in flow recipe

## Launching shards

In Cursor (or your agent UI), launch each shard as a separate Task /
subagent with `run_in_background: true`. **One browser tab per shard is
mandatory** — if all agents share the same tab, run sequentially.

Use the prompt template at
[templates/shard-prompt.md](templates/shard-prompt.md). Per launch:

1. Customize the `## Your shard ONLY` table to one row (the assigned
   letter).
2. Paste the shared artifacts block from the write-path shard.
3. Give the agent a fresh persona suffix (`+runMMDD-shardX`).
4. Pre-assign each shard a BUG-NNN number range (e.g. A: 010–019,
   B: 020–029) so parallel filers never collide; the merge renumbers
   only if a range overflowed.

## Run the pass as a wave (when `waves` / `waves-codex` is installed)

If the orchestration skill pair `waves` (Cursor) / `waves-codex` (Codex)
is installed, run this mode as a bounded wave instead of hand-rolling the
fan-out — the shard map above is the decomposition, and the waves
discipline supplies what this mode historically lacked. The
correspondences and the QA-specific overrides:

- **Shard map = wave manifest.** One row per shard: `shard | Test IDs |
  personas | model | verification tier`. The coverage gate above is the
  waves pre-fan-out partition-sum check.
- **Write-path-first = two waves, not one burst.** Shard C (admin write
  paths) is **Wave 1, serial** — it seeds the shared artifacts. The
  dependent shards launch as **Wave 2 in parallel** only after Wave 1's
  handoff. Never apply waves' "spawn all slices at once" here; D/E/F
  depend on C's output, and parallel signups within ~30s trip auth rate
  limits (stagger launches, unique persona suffixes).
- **Run report = handoff.** Each shard writes its run report to disk and
  returns only the compact structured summary (Status / Coverage /
  counts / bugs filed / report path — see the shard prompt template).
  The coordinator reads **run-report files, not shard transcripts**; a
  shard's PASS claim is a claim, not evidence.
- **Tiered verification, not uniform spot-checks.** Auto-accept PASS
  rows from low-stakes scenarios; personally re-run the write-path and
  highest-risk Test IDs; verify every FAIL/BLOCKED claim and every
  backend-write scenario against the backend row (optimistic UI lies).
  Spend coordinator time where a wrong verdict is expensive.
- **Cheap-model routing.** Read-heavy, low-risk shards (public pages,
  copy checks, static negative tests) can run on the `scout` role from
  `~/.agents/routing.json` (no routing file: the current model);
  keep the write-path shard, anything auth-heavy, and the merge/verdict
  on the `implement` role, and independent re-verification on `verify`.
  Browser-driving shards stay serial *within* the
  shard — never fan out extra browser workers inside one shard.
- **Failure ladder before sequential fallback.** A stalled or partial
  shard: (1) re-launch once, narrowed to its unfinished Test IDs with a
  fresh persona suffix; (2) if it stalls again, fall back to
  [sequential-wrapup.md](sequential-wrapup.md) for the remainder — which
  is simply the bounded second wave (batch remaining scenarios and
  fixed-bug re-tests into 1–3 scoped workers). Never write the verdict
  while a shard's scenarios are unaccounted for; the coverage gate's
  counts are the completion gate at merge time.
- **Waves cannot replace the browser.** QA evidence comes from driving
  the live app; read-only exploration workers can stage data, audit
  copy against the spec, or cross-check backend rows, but a scenario is
  only PASS with real-app evidence. Interactive BRB stays in its own
  session regardless of orchestration.

Token discipline for the run (applies with or without waves): all
evidence — screenshots, console dumps, snapshots — goes to disk under
`assets/BUG-NNN/` or the run report, never inline into chat returns; the
coordinator's context should hold shard summaries and the merge, nothing
larger.

## While shards run

- Wait for completion notifications (they fire when a subagent
  finishes); don't tail full shard transcripts into your own context —
  read each shard's **run report file** when it lands instead.
- Spot-check **critical paths** yourself — the highest-risk Test ID for
  this phase. Even if a shard reports PASS, run the one or two
  highest-risk scenarios as coordinator.
- Read backend MCP / dashboard to verify rows match expectations.
- Note any cross-shard observations (e.g. all shards saw same console
  warning) for the merge.

## Hand off if shards stall

The 2026-05-19 Mokuhoe run had 3 of 5 parallel agents stall on Clerk
rate-limits. The fix is **not** to relaunch them all in parallel. For a
*single* stalled shard, one narrowed re-launch (unfinished Test IDs only,
fresh persona suffix, after the rate-limit window passes) is worth one
try. For multiple stalls — especially rate-limit stalls, which parallel
retries make worse — switch to
[sequential-wrapup.md](sequential-wrapup.md). Write what's done into a
coordinator merge stub, then trigger the sequential pass. Either way,
account for every scenario: the coverage-gate counts are the completion
gate at merge time.

Signs of stall:
- Agent's last 5 minutes of output is the same retry loop
- "Too many requests" / 429 / "no sign in attempt was found"
- Browser refs going stale repeatedly

## Merge

When shards finish (complete or stalled with partial data):

1. Collect every `docs/qa/runs/QA-<letter>-run-YYYY-MM-DD.md`
2. Apply [gate-merge.md](gate-merge.md)
3. Verdict goes in `docs/qa/runs/COORDINATOR-MERGE-YYYY-MM-DD.md`
4. **Regenerate the HTML report** per
   [html-report-style-guide.md](html-report-style-guide.md): dashboard
   + per-bug + per-run pages.
5. If a tracker is configured, run:
   ```bash
   bash ~/.agents/skills/running-bug-review-board/scripts/bugs-needing-sync.sh "$REPO_ROOT"
   ```
   Push each listed bug per [issue-trackers.md](issue-trackers.md). Fill
   in the merge doc's "Tracker sync (this pass)" table.

## Common pitfalls (observed)

| Symptom | Cause | Fix |
|---------|-------|-----|
| "No sign in attempt was found" | Two agents in one tab → state mismatch | One tab per agent, or sequential |
| "Too many requests" on verify-email | Multiple parallel signups within 30s | Stagger 30s; use unique `+runMMDD-X` suffixes |
| Wrong account edits mid-run | Shared cookies between shards | Don't share tabs |
| Bug filed in wrong number sequence | Two agents picked same BUG-NNN | Coordinator assigns ranges or merges renames at end |
| Shard reports PASS but DB shows nothing wrote | Optimistic UI — agent didn't verify backend | Add backend-row check to scenarios |

## Shard prompt

Use [templates/shard-prompt.md](templates/shard-prompt.md). Fill in:

- `{PHASE_NUM}`
- `{SHARD_LETTER}` and `{SCENARIO_IDS}` and `{PERSONAS}`
- `{SHARED_ARTIFACTS}` (from the write-path shard output)
- `{RUN_DATE}` (YYYY-MM-DD)

## Coordinator self-check before merging

Before writing the verdict:

- [ ] Did I personally re-run the highest-risk Test ID?
- [ ] Did I verify backend state for at least one write-path scenario?
- [ ] Did I read every shard's run report (not just the chat summary)?
- [ ] Are bug numbers contiguous and titles unique?
- [ ] Are screenshots committed under `assets/BUG-NNN/`?
- [ ] Did each shard hit the "Recommended engineering priority"
      section, or did I synthesize one?

If any answer is no, do that before declaring YES/NO.
