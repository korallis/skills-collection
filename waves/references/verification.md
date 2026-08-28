# Verification Playbook

Verification is the manager's highest-leverage job in a multi-agent run.
Workers generate candidate findings; the manager decides what is allowed into
the synthesis. A worker's `Status: success` is a claim, not evidence.

The core idea: capability is roughly `base capability x gradeable signal`.
Checking a claim is often much cheaper than producing it, and multi-wave work
compounds errors. One unchecked bad handoff can contaminate every later
decision.

This playbook is strongest on objective, checkable work: counts, code, tests,
facts with sources, citations, generated files, deployments, and metrics. For
taste or judgment, verify the sub-claims and evidence; do not fake a crisp grade
for subjective preference.

## 1. Verify Before You Spawn

Run a pre-fan-out gate after discovery/staging and before delegation:

- Count total rows, messages, files, routes, modules, or records.
- Print each slice's bounds: ID range, date range, path set, or question set.
- Confirm partition sums: all slice counts add back to the total.
- Check gaps and overlaps: no duplicate ranges, missing rows, empty chunks, or
  bad sort order.
- Fix centrally, then re-run the gate.

Example:

```text
total messages: 3097
chunk-1: ids 1-388, 388 msgs, 2026-03-10..2026-03-22
chunk-2: ids 389-776, 388 msgs, 2026-03-22..2026-04-03
...
partition sum: 3097/3097
duplicates: 0
gaps: 0
```

If the gate does not reconcile, do not spawn workers yet.

## 2. Cheap Checks on Every Handoff

Every handoff gets a fast manager-side pass:

- Evidence exists for each key finding.
- File paths, URLs, message IDs, commands, or metrics resolve. Research workers
  hallucinate roughly 3-13% of citation URLs and 5-18% don't resolve at all; a
  cheap URL-health pass before trusting links cuts non-resolving citations to
  under 1%.
- The cited evidence actually supports the claim.
- Scope matches the assigned slice.
- Headline numbers can be re-counted or queried.
- Findings do not contradict another worker without being marked contested.
- The worker carried confidence tags and unresolved gaps.

Accept only findings that are evidence-backed, scope-correct, and not
contradicted. Re-task or verify the rest (often a quick follow-up wave); demote
only when re-checking isn't worth it.

## 3. Push Self-Checks Into Worker Prompts

Make every worker do cheap verification before returning:

- Cite-or-drop every important claim.
- Mark per-finding confidence: `high`, `med`, or `low`.
- Report coverage: `read 388/388`, `checked 12/12 files`, or explain skips.
- Use live/current sources for versioned APIs, pricing, schedules, product
  behavior, laws, and docs.
- Flag anything it could not verify.
- For a single important number, pick, or label (not prose), re-derive it
  independently several times (5-10 samples with real sampling variation, not
  repeated greedy calls) and report the majority plus how many agreed. Most of
  the gain arrives in the first handful; low agreement is itself a
  low-confidence flag.
- For a top claim, factored self-verification: draft, list open check questions
  ("When did X ship?", not yes/no -- models tend to agree with whatever a
  yes/no question asserts), answer each in a fresh context without the draft,
  cross-check the answers against the draft, then revise.

Avoid vague "double-check yourself" prompts. Self-correction without an
external signal degrades reasoning -- models flip correct answers to wrong more
often than the reverse. Give the worker an external check: a test, query,
source URL, schema, command, count, or separate verifier. Never let a retry
loop's stop condition peek at the expected answer (that measures the answer
key, not the worker). Budget rule: at equal cost, k independent samples plus a
majority vote usually beats critique/debate loops -- benchmark any added loop
against that baseline.

## 4. Use Dedicated Verifier Workers

Verification is a narrower job than generation. Spawn a verifier when a claim is:

- High-stakes or user-actionable.
- Citation-heavy.
- Surprising, contested, or contradictory.
- Low-confidence or single-sourced.
- A number, benchmark, count, or pass/fail claim the synthesis depends on.

Give the verifier:

- Atomic claim(s).
- Cited sources or commands.
- Acceptance question.
- Any required current-doc lookup.

Do not give it the generator's reasoning. That makes it less likely to inherit
the same mistake.

Make the verifier's job robust:

- Reference-guided + chain-of-thought: give it a rubric or reference and have it
  reason step-by-step before the verdict. Removing the reference is the biggest
  judge-accuracy drop; CoT-before-verdict helps broadly.
- Anti-gaming: never show the generator the verifier's rubric, and prefer a
  verifier that can re-derive/execute over one that re-reads prose (verifiers get
  gamed; over-optimizing a weak proxy verifier makes true quality fall).
- Hide authorship and order: never tell the verifier which worker or model
  produced a claim -- judges strongly prefer whatever is labeled as their own,
  and swapping the label flips the preference. For pairwise comparisons, run
  both orderings and average; paraphrasing a candidate before judging also
  blunts self-preference.
- Keep the judge on task: for reference-matching checks ("does the answer match
  the staged data?"), instruct the verifier to match against the reference only
  and not inject outside knowledge -- strong models over-reason on what is
  essentially entailment checking.
- Different family (optional, strongest): a same-family verifier can self-prefer
  even with an isolated context -- models recognize and favor their own output,
  and the more capable the model, the stronger the effect. For the
  highest-stakes calls, pick a reviewer/verifier route whose `family` differs
  from the author's. Read `family` from `~/.agents/routes.json` written by
  `bin/agent-routes scan`, preferring `sourceKind: harness`; never guess model
  slugs. A small panel of judges from disjoint families (majority vote on
  binary verdicts, average on scores) beat a single frontier judge on human
  agreement while cutting intra-model bias and cost. (Planned as a default in a
  later version pending testing; for now an opt-in escalation.)

The verifier returns:

- `supported`
- `partly-supported`
- `unsupported`
- `source-not-found`

For many claims, if the harness has a batch or CSV spawn, use it: one row per
claim, one verifier worker per row. Otherwise spawn one verifier worker per
claim in bounded waves. Respect the harness worker concurrency cap; if unknown,
batch 3-8.

## 5. Measure and Cross-Check

Prefer direct oracles over prose review:

- Run tests, type checks, linters, validators, parsers, or smoke scripts.
- Recount from source data rather than trusting a summary.
- Re-run queries or regexes for headline numbers.
- Use at least two independent sources that ENTAIL the claim before treating it
  as verified - check entailment, don't just count citations (a citation being
  present is not the claim being supported; even strong models lack full
  citation support on roughly half of long-form answers). Agreement compounds
  only under real independence: three independent ~90%-accurate checks give
  ~97% by majority vote, but a shared model family or shared search results
  breaks the assumption - diversify both.
- Split long claims into atomic facts, rewrite each to be self-contained
  (resolve pronouns and vague references - the step most retellings skip), and
  verify each separately. Sentence-level checks are too coarse: a large share
  of sentences mix supported and unsupported facts. A cheap model with search
  access is a strong fact-rater (it beat crowdworker annotators at a fraction
  of the cost); the verifier does not need to be frontier-class when it has an
  oracle to consult.
- Panel / multi-pass cross-check: for a high-stakes or contested claim, run it
  across several independent passes (or routes whose `family` differs, from the
  scan) and synthesize consensus vs lone-result. That extra spawning is worth it
  for claims the deliverable hinges on.

For docs/current behavior, use primary sources first. For current product or API
behavior, prefer that vendor's primary docs and live tools; do not special-case
any one vendor CLI as this skill's runtime.

## 6. Verify the Deliverable

Before declaring done:

- Run or validate the thing produced.
- For web/UI, check local routes, status codes, console errors, screenshots, and
  sibling-route regressions.
- For documents/configs/diagrams, run parsers or schema validators when possible.
- Re-read or grep critical files you wrote; do not assume a write landed.
- Confirm deployment or infra state after command success.
- Keep unverified claims labeled in the final output.

## 7. Acceptance and Escalation

Use this ladder:

1. Auto-accept: high-confidence, evidence-backed, source-resolving, corroborated.
2. Verify: medium confidence, single source, important citation, contested.
3. Escalate: low confidence, unresolved, contradictory, high-stakes.

Escalation order:

1. Re-task narrower.
2. Spawn a verifier.
3. Use a higher-capability reviewer/verifier route from the scan.
4. Ask the user. Mark the limitation explicitly
   only as a last resort, after re-tasking and verifier passes are exhausted.

Never launder low confidence into confident prose. Final claims should be marked
`verified`, `single-sourced`, or `unverified` when the distinction matters.

## Harness-Agnostic Verification Surfaces

- A read-only verifier or explorer worker for local source checks.
- Docs, web, or MCP tools for current sources.
- Row-shaped verifier batches if the harness has them; otherwise one verifier
  worker per claim.
- Tests, validators, shell commands, browser checks, and direct file reads.
- The harness's code-review surface if present.

Do not assume the harness auto-grades handoffs. Treat verifier workers and
external oracles as the portable path.

## Example: Codex verification surfaces

- `explorer` or a custom read-only `verifier` agent for local source checks.
- `default` or custom docs researcher for current docs/web/MCP source checks.
- `spawn_agents_on_csv` for verifier-per-row batches when available.
- `codex exec --output-schema` for scripted verification artifacts.
- Tests, validators, shell commands, browser checks, and direct file reads.
- Codex `/review` and GitHub code review for code-risk review.
- `approvals_reviewer = "auto_review"` for approval/security review only. It
  does not verify arbitrary claims.

## Grounding (Sources for the Techniques Above)

- Factored self-verification and open-not-yes/no check questions:
  Chain-of-Verification, arXiv 2309.11495 (Findings of ACL 2024).
- Sample-and-majority-vote with agreement as a confidence flag:
  Self-Consistency, arXiv 2203.11171 (ICLR 2023).
- Intrinsic self-correction degrades reasoning; debate loses to
  self-consistency at matched budget; never gate a loop on the answer key:
  arXiv 2310.01798 (ICLR 2024).
- Atomic-fact decomposition with self-contained rewrites and search-backed
  rating: SAFE / LongFact, arXiv 2403.18802 (NeurIPS 2024).
- Judges recognize and favor their own output; hide authorship, swap orderings:
  arXiv 2404.13076 (NeurIPS 2024).
- Panel of judges from disjoint model families beats one big judge on human
  agreement, bias, and cost: PoLL, arXiv 2404.18796 (industry preprint).
- Citation presence is not claim support; check entailment: FActScore, arXiv
  2305.14251; ALCE, arXiv 2305.14627 (both EMNLP 2023).
- Research agents fabricate 3-13% of citation URLs; URL-health passes fix most:
  arXiv 2604.03173.
- Verification-driven replanning as the orchestration-level coordination
  signal; stop on completeness / diminishing returns / budget, not fixed
  iteration caps; most replans are retries of incomplete slices: VMAO, arXiv
  2603.11445.
- Verification as a scaling axis (continuous verifier scores improving along
  score granularity, repeated evaluation, criteria decomposition):
  LLM-as-a-Verifier, arXiv 2607.05391.
- Centralized verification contains error amplification (4.4x under a
  coordinator bottleneck vs 17.2x for unchecked independent agents;
  multi-agent hurts sequential-reasoning tasks): arXiv 2512.08296.
- Compaction silently drops in-context constraints (0% -> 30-59% violations
  post-compaction; pin constraints verbatim through summaries): Governance
  Decay, arXiv 2606.22528.
- Team-size scaling: homogeneous teams plateau (hard ceiling for
  instruct-class models on bounded tasks, correctness level; diversity is the
  lever; an N<=5 pilot identifies the regime): arXiv 2606.02646; 2 diverse
  agents can match 16 homogeneous: arXiv 2602.03794.
- Convergence-based early stopping beats fixed `max_iterations` at parity
  quality; per-round judge gating is counterproductive: arXiv 2606.27009.
