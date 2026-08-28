# Evals for `waves`

Behavior evals for the orchestration skill, following the eval methodology
Anthropic ships in its `skill-creator` skill and skill-authoring docs
(evaluation-driven development: identify gaps, write scenarios, baseline,
iterate). Because `waves` is an *orchestration* skill, the unit under
test is the **transcript** -- how the manager decomposed, fanned out,
verified, and synthesized -- not just the final artifact.

This skill was formerly named `waves-codex`.

## What's Here

- `evals.json` -- the scenarios. Format follows the skill-creator convention:
  `skill_name` plus a list of evals, each with `id`, `name`, `prompt`,
  optional `files` (paths relative to the skill root), `expected_output` (one
  sentence describing a good run), and `expectations` -- objectively gradeable
  PASS/FAIL statements about the transcript or output.
- `files/` -- fixtures with known ground truth so grading can be programmatic:
  `support-tickets.csv` (40 rows; 12 login-timeout, 9 export-failure, 6
  dark-mode, 5 billing, 8 misc) and three pre-written worker handoffs, one of
  which (`handoff-chunk-2.md`) contains a deliberately wrong count (billing
  "9 of 20", actual 3) and a phantom citation (`T-058` does not exist).

## How to Run (A/B Protocol)

For each eval, run the prompt twice in fresh harness sessions (whatever
agent CLI this eval is run in) and save both transcripts:

1. **With skill** -- a session where `waves` is installed (the prompts
   already say "Use the waves skill").
2. **Baseline** -- an identical fresh session without the skill installed
   (drop the "Use the waves skill" prefix). When comparing two
   *versions* of the skill, the baseline is the previous version instead.

Save the full transcript the way this harness records a session.

### Example: Codex transcript export

`codex exec --json` is useful when a script needs the transcript as stable
events. That is one harness's export syntax, not the required runner.

Fresh sessions matter: leftover context from authoring or a prior run masks
gaps. Copy any `files` fixtures into the session workspace first so relative
paths resolve. Suggested layout, per skill-creator:

```
waves-workspace/iteration-N/eval-<id>/{with_skill,without_skill}/
    transcript.md   # full session transcript as this harness records it
    output.md       # final deliverable only
    grading.json    # graded expectations (below)
```

Note on triggering: this skill is opt-in because a run spawns more workers
than usual (`disable-model-invocation` is a common way to keep invocation
explicit). There is no trigger-accuracy suite. Sanity-check that invoking
the skill by name actually loads it.

## Grading Rules

Adapted from skill-creator's grader; grade each expectation independently:

- **PASS/FAIL only, no partial credit.** When uncertain, the burden of proof
  is on the expectation -- an ungraded or ambiguous expectation is a FAIL.
- **Cite evidence.** Every verdict quotes the transcript step or output line
  that settles it.
- **Prefer programmatic checks.** Anything countable (the 40-row total, the
  12/9/6/5 theme counts, the 3-vs-9 billing recount, the phantom `T-058`)
  should be re-derived by script or query, not eyeballed.
- **Blind the grader.** The grader sees one transcript at a time and is not
  told which configuration produced it; never reveal which model or config
  authored a transcript (judges favor output labeled as their own).
- **Grade the evals too.** Flag expectations that pass in *both*
  configurations (non-discriminating -- the base model already does it), fail
  in both (broken or too strict), or flip run-to-run (flaky). Rewrite or drop
  them.

## Aggregate and Compare

Summarize per configuration -- pass rate per eval and overall, plus time and
token cost when available -- and report the delta (skill minus baseline), the
same shape as skill-creator's `benchmark.json`. The skill earns its context
window only if the delta is real.

## Iterate

- Read the **transcripts**, not just the outputs -- orchestration failures
  (busy-polling, thin worker prompts, skipped coverage gates, recursion-cap
  confusion) are visible mid-run, not in the final report.
- Generalize from failures; don't patch in example-specific rules. Keep the
  SKILL.md lean -- remove guidance that isn't changing behavior.
- If a failure repeats across evals, that section of the skill needs
  restructuring, not another MUST.
- **Retirement check:** if the baseline starts passing the expectations
  without the skill, the base model has absorbed that behavior -- trim or
  retire the corresponding guidance rather than letting the skill bloat.

## Extending the Set

Start small, expand after each round (the first runs usually reveal better
assertions than you could write up front). Good expectations are objectively
verifiable, specific, and countable; subjective quality (synthesis prose
style) is better judged qualitatively than forced into assertions.
