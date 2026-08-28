# Advanced wave patterns

Loaded on demand from `SKILL.md`. Each section stands alone.

## CSV / Row Fan-Out

When the work is naturally one row per worker — files, incidents, packages,
PRs, migration targets, messages, customer records, or claims to verify — use
the harness batch/CSV spawn if it is present; otherwise spawn one worker per
row, batched under the concurrency cap.

Manager responsibilities:

- Create a table/CSV with a stable id column.
- Put enough per-row context in columns for a self-contained prompt.
- Provide an instruction template with column placeholders.
- Provide an output schema when downstream synthesis needs machine-readable
  results.
- Require each worker to return once in the handoff (or harness job-result)
  shape.
- Cap concurrency at the harness worker limit (if unknown, batch 3-8).

For a verifier pass, build `claims.csv` with `claim_id`, `claim`, `sources`,
`acceptance_question`, and optional `stakes`. Require JSON fields: `verdict`,
`evidence`, `source_status`, `correction`, `confidence`, and `gaps`.

## Generate-and-Filter and Tournaments

For open-ended ideation or "produce the single best X", generate several
candidates and filter rather than trusting one attempt:

- Cheap filter first: gate candidates through a near-ground-truth check (tests,
  schema/exec, dedup/clustering) before spending judge tokens. Generation is
  cheap; judging is not.
- Selection ladder, not all-pairs: dedup/cluster -> shortlist -> pairwise-judge
  only among finalists. A naive O(N^2) tournament wastes tokens on also-rans.
- Competing implementations: use isolated git worktrees and one worker process
  per attempt, then inspect/test/merge the winner.
- Budget check: at equal cost, k independent attempts plus a majority vote or
  cheap filter usually beats critique/debate loops -- benchmark any iterative
  loop against that baseline before paying for it.

## Parallel Writes

Workers are a good fit for parallel write work when you use worktrees, separate
sandboxes, or disjoint ownership. Still treat write coordination as a real
merge problem:

- Read/research/test/log analysis: safe default.
- Disjoint edits in one checkout: acceptable when ownership is explicit and
  paths do not overlap.
- Overlapping edits: avoid. Have workers propose handoffs, then implement
  serially.
- Competing implementations: isolated git worktrees, one worker process per
  worktree.
- Always inspect and test the merged result in the manager thread.

## Native Verification Surfaces

Use these where they fit:

- Tests, validators, type checks, linters, browser checks, and direct source
  recounts are the strongest verification signals.
- Dedicated verifier workers are the native replacement for a claim-check
  pass; prefer a different `family` from the author when independence matters.
- A row-shaped verifier pass (batch/CSV spawn if present, else one worker per
  row) is ideal when many claims need the same acceptance question.
- Prefer a deterministic validator or schema when another process needs
  machine-readable results.

## Escalating Beyond One Interactive Thread

Use this skill for interactive, bounded fan-out inside one task.

If the harness offers durable threads, the same handoff discipline applies:
message a worker thread and require the structured handoff back; never pull a
full worker transcript into the coordinator. Reuse a worker thread only for
its own lane, never for an unrelated slice. Otherwise use ordinary workers.

For scripted or CI-style fleets, run one worker process per git worktree with
explicit sandbox and route settings. Prefer machine-readable results when
another script needs stable events.

For always-on, team-scale orchestration, use the Symphony pattern: an issue
tracker or queue as the control plane, one agent workspace per item, bounded
concurrency, retries, observability, and human review. Treat Symphony as a
reference/spec pattern, not a drop-in replacement for this interactive skill.
