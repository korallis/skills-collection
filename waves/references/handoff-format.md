# Worker Handoff Format

A worker's final message is its handoff. Put everything important in it;
intermediate output may be invisible, noisy, or too expensive for the manager to
reconstruct. End every worker prompt by pasting one of these templates and
saying "Use exactly this structure."

## Research / Analysis Worker

Use this for data analysis, web/MCP research, code reading, audits, test
triage, and design investigation.

```markdown
## Status
success | partial | blocked

## Scope
<the exact slice this worker owned: data range / area / paths / question>

## Coverage
- Assigned: <expected rows/files/ranges/questions>
- Read: <actual rows/files/ranges/questions, e.g. 388/388 lines>
- Skipped: <anything not read and why, or "none">

## Key findings
- [high|med|low] <finding> -- evidence: <file:line | msg id+date | URL | metric | command output summary> -- sources agreeing: <N>
- [high|med|low] <finding> -- evidence: <...> -- sources agreeing: <N>

## Sources
- <paths read, data ranges covered, URLs/docs fetched, commands run>

## Confidence & verification
- Verified: <findings re-run, recounted, or cross-checked with >=2 independent sources>
- Single-sourced: <claims supported by one source only>
- Inferred: <claims not independently checked>
- Unresolved / could not verify: <claims or citations that did not resolve>
- Would change my conclusion: <missing evidence or falsifier>

## Open questions / gaps
- <anything ambiguous, missing, contradictory, or out of scope that the manager should resolve, often by spawning a follow-up task>

## Suggested follow-ups
- <concrete next tasks the orchestrator should consider spawning>
```

## Code / Edit Worker

Use only when the worker has disjoint ownership, a separate worktree, or an
explicit isolated workspace.

```markdown
## Status
success | partial | blocked

## Changed
- <path>: <what changed and why>

## Verification
<one of: live-verified | test-verified | type-check-only | not-verified>
- <command run -> outcome / test pass-fail counts>

## Confidence & risk
- Verified: <what was directly checked>
- Unverified: <what still needs testing/review>
- Risk: low | med | high -- <why>

## Notes & deviations
- <assumptions, surprises, broken invariants, merge concerns, anything the parent must know>

## Suggested follow-ups
- <concrete next tasks the orchestrator should consider>
```

## Verifier Worker

Use this when a worker's only job is to check another handoff's claims. Give it
the claim and cited sources, but not the original worker's reasoning.

```markdown
## Status
success | partial | blocked

## Scope
<claims checked, source set, and acceptance question>

## Verdict per claim
- <claim id or claim> -> supported | partly-supported | unsupported | source-not-found
  - evidence: <quote, file:line, metric, command output, or "none">
  - source checked: <URL/path/command> (resolved: yes/no)
  - confidence: high | med | low
  - correction: <corrected claim or "drop">

## Overall
accept | revise | reject -- <one line why>

## Gaps
- <sources unavailable, ambiguous wording, missing oracle, or checks not run>
```

## CSV Batch Worker Result

When using `spawn_agents_on_csv`, each row worker should call
`report_agent_job_result` exactly once with JSON that mirrors the same contract.
Keep fields short enough to fit in the exported CSV.

```json
{
  "status": "success | partial | blocked",
  "scope": "<row id and exact slice>",
  "coverage": {
    "assigned": "<expected>",
    "read": "<actual>",
    "skipped": "<none or details>"
  },
  "key_findings": ["<finding with evidence>", "<finding>"],
  "sources": ["<path/url/range/command>"],
  "confidence_and_verification": {
    "verified": ["<claim>"],
    "single_sourced": ["<claim>"],
    "inferred": ["<claim>"],
    "unresolved": ["<claim>"]
  },
  "open_questions": ["<gap>"],
  "suggested_follow_ups": ["<task>"]
}
```

Verifier CSV rows should return JSON with:

```json
{
  "claim_id": "<id>",
  "verdict": "supported | partly-supported | unsupported | source-not-found",
  "evidence": "<quote, file:line, metric, command output, or none>",
  "source_status": "<resolved yes/no plus notes>",
  "correction": "<corrected claim or drop>",
  "confidence": "high | med | low",
  "gaps": ["<missing source/check>"]
}
```

## Prompt Endings per Worker Type

End every worker prompt with the generic block, plus the add-on for its type:

Generic (all workers):

```text
Return only the structured handoff from references/handoff-format.md. Use
exactly the headings. Include concrete evidence and confidence for every
important claim. Flag anything you could not verify.
```

Research workers, add:

```text
Use live/current sources when the fact may have changed. Do not rely on training
data for versioned APIs, pricing, schedules, product behavior, or current docs.
Flag anything you could not verify.
```

Implementation workers, add:

```text
You are not alone in the codebase. Other workers may be active. Own only the
files/modules listed above, do not revert changes you did not make, and adjust
to nearby changes if you encounter them.
```

Verifier workers, add:

```text
Your job is verification, not generation. Check only the assigned claim(s)
against the provided source(s) or oracle(s). Do not use the original worker's
reasoning. Return supported, partly-supported, unsupported, or source-not-found
with exact evidence.
```

## How the Manager Reads a Handoff

1. `Status` is not `success`: decide whether to retry, narrow scope, repair
   inputs, or mark the limitation in the final synthesis.
2. `Coverage`: verify the worker covered exactly its slice.
3. `Key findings`: every important claim needs evidence and a confidence tag.
   Claims without traceable evidence are unverified.
4. `Sources / Confidence & verification`: preserve them so later waves and the
   final deliverable can trace evidence. Route low-confidence, single-sourced,
   contested, or unresolved citations to a verifier.
5. `Open questions / Suggested follow-ups`: the richest section -- treat each
   bullet as a candidate second-wave task and accept, reject, or consolidate it.
   Spawning a focused follow-up wave for real gaps is the normal path, not an
   exception.

## Why a Fixed Shape

Uniform handoffs let many isolated workers converge without cross-talk. The
manager can merge evidence mechanically instead of re-deriving structure from
freeform prose.

## Carrying a Handoff Into the Next Wave

When one wave feeds another, pass forward only a distilled, verified handoff --
the accepted findings plus a one-line critique -- never raw transcripts or
rejected candidates. Long, irrelevant context measurably degrades the next
wave's reasoning; the synthesize barrier is where you compress. Multi-wave is
the normal shape, not an exception: a realistic run is often `12 + 3 + 1`
workers across waves, each wave spending the previous wave's verified findings.

One exception to compression: constraints are pinned, never summarized. The
wave manifest, stop conditions/budget, and safety/scope rules travel verbatim
through every synthesis file and compaction -- measured compaction behavior
silently drops in-context constraints (violations rising from 0% to 30-59%
post-compaction; pinning restores 0% -- arXiv 2606.22528).
