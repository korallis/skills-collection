# Worked Example and Decomposition Recipes

## Worked Run: Analyze Messages and Build a Roadmap

Goal: read a user's message history, find patterns/goals/frustrations, research
the relevant product stack, and produce a roadmap.

The upgraded reference pattern is multi-wave, not one burst: 16 workers across 3
waves.

- Wave 1: 8 message chunks, 1 workspace reader, 3 research streams.
- Wave 2: 3 focused Convex deep-dives after the user narrowed scope.
- Wave 3: 1 iOS MVP worker after synthesis exposed a concrete product slice.

The serial staging phase was the largest phase: export, clean, chunk, verify
counts and date ranges, fix a timestamp-sort issue, then fan out.

### Step 0 - Discover Serially

- Locate the data store: SQLite, JSONL, exports, or transcript files.
- Read schema and sample messages.
- Count rows and date coverage.
- Inspect nearby workspace memory/config if relevant.
- Verify the pre-fan-out gate: chunk counts sum to the total, each chunk has
  disjoint bounds, no duplicates/gaps, and date ranges make sense.
- Result: about 3,000 messages, chunked into 8 equal message-count ranges, plus
  4 research or workspace streams.

### Step 1 - Decompose

- 8 data-chunk workers: equal message-count ranges, not equal calendar time.
- 1 workspace reader: memory/config/workspace files.
- 3 research workers: realtime voice stack, Notion/platform SDK, iOS/on-device
  options.

### Step 2 - Fan Out with Harness Workers

Use explicit manager wording:

```text
Spawn 12 workers in parallel the way this harness dispatches workers, and wait
for all of them before synthesis. Use explorer roles for the 8 read-only
message chunks and workspace reader. Use research roles for the 3 stack
research streams. Each worker must return the research/analysis handoff
format from references/handoff-format.md, including Coverage and
Confidence & verification sections.
```

Example data worker prompt:

```text
Overall goal, context only: find patterns, goals, frustrations, and recurring
workflows in a user's chat history with their assistant to inform an app roadmap.

Your slice: messages with id 1001-1500 only in /path/to/messages.sqlite.

Do: read only that disjoint range. Extract recurring topics, stated goals,
repeated pain points, and workflows the user performs often. Quote message id
and date as evidence.

Coverage rule: report messages read as <actual>/<assigned>. If you skip any
message, list why.

Verification rule: cite-or-drop every finding, tag confidence high|med|low, and
separate verified, inferred, single-sourced, and unresolved claims.

Do not: analyze other message ranges, write files, or produce the final roadmap.

Return exactly the research/analysis handoff format.
```

Example research worker prompt:

```text
Overall goal, context only: build a low-latency realtime voice companion app.

Your slice: research realtime voice stack options only, including current OpenAI
Realtime APIs, proxy/SDK options, and latency tradeoffs. Use available docs/web
or MCP tools. Include source URLs and dates where relevant.

Verification rule: use live/current sources, not training data. Cite-or-drop
claims, tag confidence high|med|low, and say what could not be verified.

Do not: compare all roadmap options or write implementation code.

Return exactly the research/analysis handoff format.
```

### Step 3-5 - Collect, Verify, Spawn Next Waves, Deliver

- Read all handoffs; check coverage against assigned slices; spot-check citations
  and source paths; recount headline numbers from the source data.
- Send contested, high-stakes, or citation-heavy claims to a verifier worker.
- Merge recurring themes across message chunks; separate evidence-backed patterns
  from one-off observations; reconcile stack-research conflicts by source quality
  and date.
- Spawn the next wave from what the handoffs surfaced -- treat each
  `Suggested follow-ups` bullet as a candidate task. Here that is Wave 2 (3
  Convex deep-dives once the user narrowed scope) and then Wave 3 (1 iOS-MVP
  worker once synthesis exposed a concrete slice). Planning for a second and
  third wave is the default, not the exception.
- Synthesize the roadmap yourself from the merged, verified handoffs.

## Recipe: Decomposition of a Vague Build

Use when a single high-level request ("build a Flappy Bird game") must expand
into understanding + plan + subtasks.

1. Locate the entropy. Specification unknowns (web or native? which
   engine/framework? scope -- one screen, score, difficulty curve?) vs
   environment unknowns (what is already in the repo? build tooling? asset
   pipeline?).
2. Reduce it cheaply. Dig locally (read the repo, package manifest, existing
   scaffolding). For anything the repo cannot answer, spawn a small scouting wave
   (one `explorer` per candidate engine/framework) on a cheaper/faster harness
   route from `~/.agents/routes.json` written by `bin/agent-routes scan`
   (prefer `sourceKind: harness`), and verify. State assumptions for
   specification gaps ("web canvas, vanilla TS, one screen + score") instead of
   blocking -- ask only the one question whose answer would change the whole
   plan.
3. Decompose least-to-most. The plan is now low-entropy: game loop -> render
   pipes/bird -> input + gravity -> collision -> score/state -> polish.
   First-order subtasks first; each verified piece lowers uncertainty for the
   next.
4. Execute in waves. Build with disjoint-ownership `worker`s (or serially -- see
   "Parallel Writes"), verify the artifact, and open another scouting
   sub-wave only where a subtask is still high-entropy.

## Recipe: Data-Chunk Fan-Out

Use for large corpora: messages, tickets, logs, transcripts, documents, or
analytics rows.

1. Discover total size and schema.
2. Split into disjoint ranges or files.
3. Verify total count, per-slice bounds, gaps/overlaps, and partition sum.
4. Spawn one `explorer` per chunk. If the harness has a row-shaped batch spawn,
   use it; otherwise one worker per row.
5. Require coverage and evidence identifiers in every finding.
6. Merge into themes, counts, outliers, and follow-ups; spawn a focused second
   wave for the follow-ups that change the deliverable.

CSV-shaped prompt:

```text
Create /tmp/messages.csv with columns chunk_id, start_id, end_id, db_path.
Then use a row-shaped batch spawn if the harness has one; otherwise one worker
per row. Each worker analyzes messages {start_id}-{end_id} in {db_path} and
returns JSON with status, scope, coverage, key_findings, sources,
confidence_and_verification, open_questions, and suggested_follow_ups.
```

Verifier pass:

```text
Create /tmp/claims.csv with columns claim_id, claim, sources, acceptance_question.
Then use a row-shaped batch spawn if the harness has one; otherwise one worker
per row. Each worker verifies claim {claim_id}: {claim}, checks only {sources},
answers {acceptance_question}, and returns JSON with verdict, evidence,
source_status, correction, confidence, and gaps.
```

### Example: Codex spawn_agents_on_csv

One harness's syntax for the same CSV column design:

```text
Create /tmp/messages.csv with columns chunk_id, start_id, end_id, db_path.
Then use spawn_agents_on_csv if available:
- csv_path: /tmp/messages.csv
- id_column: chunk_id
- instruction: "Analyze messages {start_id}-{end_id} in {db_path}. Return JSON
  with status, scope, coverage, key_findings, sources,
  confidence_and_verification, open_questions, and suggested_follow_ups via
  report_agent_job_result."
- output_csv_path: /tmp/message-analysis-results.csv
- max_concurrency: 6
```

```text
Create /tmp/claims.csv with columns claim_id, claim, sources, acceptance_question.
Then use spawn_agents_on_csv if available:
- csv_path: /tmp/claims.csv
- id_column: claim_id
- instruction: "Verify claim {claim_id}: {claim}. Check only these sources:
  {sources}. Answer this acceptance question: {acceptance_question}. Return JSON
  with verdict, evidence, source_status, correction, confidence, and gaps via
  report_agent_job_result."
- output_csv_path: /tmp/claim-verification-results.csv
- max_concurrency: 6
```

## Recipe: Multi-Stream Research

Use for comparisons and roadmaps.

1. Define one worker per technology, vendor, API, or approach.
2. Workers research their own option only.
3. Require source URLs, version/date notes, and confidence labels.
4. Split huge topics when one question list would blow context.
5. The manager performs the comparison and recommendation.

Good slices:

- "Research OpenAI Realtime and current SDK/proxy constraints."
- "Research Notion API/SDK fit for this workflow."
- "Research iOS background audio and on-device model constraints."
- "Research Convex auth and limits."
- "Research Convex core idioms."
- "Research Convex components and ecosystem fit."

## Recipe: Whole-Repo Audit

Use for broad audits where one lens would be slow or noisy.

Split by dimension:

- Security and auth.
- Data correctness.
- Performance and concurrency.
- Dead code and dependency risk.
- Test coverage and CI gaps.

Or split by module:

- `apps/web`
- `apps/api`
- `packages/db`
- `packages/ui`

Default to read-only `explorer` or custom reviewer agents. The manager produces
a severity-ordered report with file references and confidence labels.

## Recipe: Parallel Implementation

Use only when ownership is clear.

Safer patterns:

- One `worker` owns frontend components, another owns backend API, another owns
  tests.
- One worktree per competing implementation.
- One isolated worker process per git worktree for scripted attempts.
- One verifier or reviewer pass checks the merged result before final delivery.

Risky patterns:

- Multiple workers touching the same file family.
- Multiple workers changing shared contracts without a manager-owned design.
- Workers editing before discovery converges.

## Recipe: Implement a Reviewed Plan (Plan -> Edit Wave -> Verify Wave)

The end-to-end SWE shape -- three waves with different jobs:

1. Wave A -- spec. A small wave (or the manager alone) turns the goal into a
   written plan: ordered subtasks, explicit file ownership per subtask,
   `Done when:` criteria. Verify it (the artifact-then-bigger-wave shape); the
   verified plan is the contract every edit worker anchors to.
2. Wave B -- disjoint edits. One `worker` per plan subtask with strictly
   disjoint path sets (or one worktree per competing design). Each prompt
   carries the plan excerpt for its subtask, its exact paths, the "you are not
   alone" warning, and the code/edit handoff format. Pick a capable coding
   route from `~/.agents/routes.json` written by `bin/agent-routes scan`
   (prefer `sourceKind: harness`).
3. Wave C -- verify. Read-only workers run the oracles: tests, type checks,
   lint, a reviewer pass over the combined diff, regression checks on sibling
   routes. Route failures back as narrow fix tasks (bounded -- don't loop).
   The manager merges, re-reads critical files, and delivers.

Interleave cheaply: Wave C slices that only touch Wave B's finished subtasks
can start while slower edits finish. Keep the plan in the harness plan/todo
surface and the per-subtask status in the wave manifest.

## Recipe: Codemod / Migration Across Many Files (Row-Shaped)

When the same mechanical change applies to N files/callsites (rename an API,
swap a client, migrate a schema field):

1. Stage the target list. Grep/list the exact targets into
   `.waves/<run>/targets.csv` (path, symbol, line hints). Verify the count --
   the list is the coverage gate.
2. Fan out the edits: if the harness has a row-shaped batch spawn, use it with
   one row per target; otherwise one worker per row (or batches of 3-8
   `worker`s each owning a disjoint file subset); prompts point at list rows,
   not pasted code.
3. Verify by oracle, not prose: after each batch, re-run the grep (old
   pattern count must fall to the expected residue), then tests/type checks.
   A row-shaped run with a cheap oracle is the one place going wider than
   usual is safe.

## Recipe: CI-Failure Triage (Diagnosis, Then One Fix Wave)

For a red CI run with several failing jobs: one read-only `explorer` per
failing job/log bundle (disjoint), each returning root-cause hypothesis +
evidence (log lines, commit range) + confidence. The manager dedupes root
causes across jobs (one bad commit often explains several failures), sends
contested diagnoses to a verifier, then runs a single fix wave with disjoint
ownership -- and re-runs CI as the deliverable check.

## Wave Shapes

A wave is not one move - pick the shape from how much you know about the problem.

- Decomposition / scouting wave (reduce entropy before the big wave): when the
  goal is vague or high-entropy ("build a Flappy Bird game", "make it faster"),
  the first wave's job is to reduce uncertainty, not build. Dig locally, then fan
  a small scouting wave at the unknowns (stack, constraints, current APIs, repo
  shape) on a cheaper/faster harness route from `~/.agents/routes.json` written
  by `bin/agent-routes scan` (prefer `sourceKind: harness`), verify, and only
  then decompose the low-entropy version into the execution wave. See
  "Entropy-First Decomposition."
- Exploratory wave (you don't know the shape yet): when the space is unmapped
  (QA, an unfamiliar repo, "what's wrong here?"), send a broad first wave - many
  workers probing different surfaces/flows at once. Its job is to find the edges,
  not finish. Verify what's real; now you know the shape.
- Shaping wave (narrow as you learn): the next wave is more focused - kill dead
  ends, double down on what had teeth. Each wave spends the previous wave's
  findings instead of re-guessing.
- Artifact-then-bigger-wave: a small wave writes an architecture doc; verify it;
  then a much bigger wave builds against the verified spec. The small wave
  de-risks the big one; the artifact keeps the big wave from poisoning itself.
- Divergent research wave: send workers in genuinely different directions on the
  same question, let them return independently, then verify across them. High
  token value with no cross-contamination - separate contexts mean the directions
  don't poison each other.

Human-in-the-loop is optional by design: read the synthesis and shape the next
wave yourself, or let the verifier gate it automatically.

## Anti-Patterns

- Fan out before discovering the shape of the task.
- Slice a high-entropy goal before reducing its uncertainty. Vague goals
  decompose into overlapping, mis-sized slices; dig locally -> pull from attached
  resources -> ask only if it pays, then slice (see "Entropy-First Decomposition").
- Fan out before verifying coverage.
- Give workers vague prompts and hope they infer context.
- Ask workers to "figure out the whole thing" instead of owning one slice.
- Let workers compare across sibling options; the manager owns cross-cutting
  synthesis.
- Trust `Status: success`; it is a claim, not evidence.
- Embed giant verbatim artifacts in a handoff. Write large artifacts to disk and
  cite the path instead.
- Skip re-reading critical files you wrote.
- Stop after one wave when handoffs surfaced real, deliverable-changing
  follow-ups. Multi-wave (`12 + 3 + 1`) is the expected shape, not one burst.
- Do not recurse by default (workers spawning workers). Recursive fan-out is
  expensive and unpredictable. Manager-driven sequential waves are encouraged,
  not capped.
- Assume parallel writes automatically merge. Use disjoint ownership or
  worktrees.
- Forward raw handoffs as the final answer.

## Grounding (Why Entropy-First Works)

Framing decomposition as uncertainty reduction is well-supported, and each
source contributes a usable mechanism -- not just a citation:

- Prefer the probe that halves the surviving interpretations. Uncertainty of
  Thoughts (UoT, arXiv 2402.03271, NeurIPS 2024) scores candidate questions by
  expected information gain and shows the best probe is the one that splits
  the remaining hypotheses ~50/50 (binary-answer entropy peaks at an even
  split). Swapping that entropy reward into a tree search -- not the search
  itself -- carried most of its +38% average success gain. Manager use: aim
  scouts at the unknown whose answer eliminates the most plans, not the one
  easiest to look up.
- Ask only when the value of asking clears a threshold. SAGE-Agent (arXiv
  2511.08798) prices each candidate question by expected value of perfect
  information minus a redundancy cost, asks only when that beats a fraction of
  its confidence in the best current interpretation, and acts once that
  confidence passes an execute threshold. Penalizing redundant questions cut
  questions asked ~18-27% with under 3% quality loss -- over-asking is
  measurably wasteful. This paper is also the explicit source of the
  specification-vs-model uncertainty split.
- Judge "is the goal fully specified?" before acting, and err toward asking.
  arXiv 2606.19559 gates clarification on a specification-uncertainty score
  emitted before choosing an action; a conservative ask-threshold silently
  failed (recall collapsed), while a generous one cost little. Two honest
  caveats it adds: every extra self-assessment channel taxed task success
  slightly, and verbalized confidence ran overconfident -- treat self-reported
  scores as rankings, not probabilities. ("Resolve environment unknowns by
  gathering via tools" is this skill's operational extension, not that paper's
  mechanism.)
- Order the plan least-to-most; invest in the decomposition itself.
  Least-to-Most (arXiv 2205.10625, ICLR 2023) solves subproblems in sequence,
  each answer feeding the next; its gains concentrate on deep problems (5+
  dependent steps -- shallow tasks gain nothing), and its own error analysis
  shows the decomposition step, not the solving, is the bottleneck -- and that
  decompositions don't transfer across domains. Plan-and-Solve (arXiv
  2305.04091, ACL 2023) shows plan-then-execute cuts missing-step errors but
  leaves misread-goal errors untouched -- which is exactly why the
  specification check above comes before planning.

These are single-model prompting results. The parallel fan-out, the
verification gates between waves, and "each verified result lowers uncertainty
for the next" are this skill's multi-agent adaptation -- the verification half
is grounded separately in `references/verification.md`.
