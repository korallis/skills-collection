# Local multi-model engineering contract

This is the normative orchestration contract for non-trivial software work routed through
`lee-engineering`. Repository instructions and explicit user authority override it.

A task is non-trivial when it changes behavior, a public or inter-module contract, architecture,
security/privacy, CI, deployment, durable state, or more than one independently owned module. A
mechanical single-file change with no behavioral or contractual effect may remain single-agent.

The coordinator MUST classify risk before dispatch as one or more of `ordinary`, `high-risk`,
`security-sensitive`, or `merge-critical`, with the triggering facts recorded. Treat deployment,
release/rollback, ingress or service-manager configuration, CI promotion, authentication/authority,
durable-state transitions, data migration, irreversible operations, and external side effects as
`high-risk` by default. Repository instructions MAY add stricter triggers.

The uppercase words MUST, MUST NOT, SHOULD, and MAY are normative. Imperatives in the parent
`SKILL.md` and repository `AGENTS.md` have the same force.

## Terms and authority

- **Coordinator:** the single user-facing context accountable for intent, authority, acceptance
  criteria, the dependency graph, and final judgment.
- **Supervisor:** a read-only background lane that watches long-running checks, CI, bounded retries,
  and worker lifecycle.
- **Specialist lead:** a persistent, bounded domain session accountable for a defined result.
- **Worker:** a short-lived session with a fixed task packet and return contract.
- **Writer lease:** exclusive permission for one agent process to edit one checkout for a declared
  scope. A branch may have sequential writers, but a checkout MUST never have concurrent writers.
- **Locally launched coding CLI:** a process invoked on the controlled host that reads and acts on the
  local checkout. Its inference may still be an external provider data route.
- **Self-hosted model:** model weights served on infrastructure controlled by the user. It is not the
  same thing as a locally launched provider-backed CLI.
- **Cloud coding agent:** a hosted/background task, provider-managed workspace or VM, remote repo
  writer, PR agent, or service that clones, edits, commits, or pushes outside the controlled local
  checkout. Cursor Cloud Agents/workers, Claude hosted/cloud sessions, and equivalent remote tasks
  are examples.
- **Model family:** the resolved underlying provider/model lineage, not the CLI name. Cursor running
  Claude is Claude-family review, not a separate Cursor family.

Skill activation, model diversity, or a required review MUST NOT create new data-route, write, GitHub,
deployment, or external-system authority. If the local-versus-cloud execution mode or actual model
route cannot be resolved, the route is unavailable.

## Evidence rules

Hard facts come from the current authoritative provider/tool documentation and actual account or CLI
configuration: model identity, limits, tool support, provider route, retention, training use, and
zero-data-retention eligibility. Community feedback or model self-assessment MUST NOT override those
facts.

For subjective task fit, use evidence in this order:

1. repeated results on a fixed, representative task from the current repository;
2. concrete community reports with a task, artifact, failure, correction, latency, or cost;
3. the model's bounded self-assessment through the installed CLI; and
4. provider capability claims or benchmark marketing.

The dated hypotheses and source register are in
[`model-evidence-2026-08-24.md`](model-evidence-2026-08-24.md). They propose evaluations; they do not
admit a route or select a writer.

Preserve an existing admitted writer lease. For a new writer, use an explicit user selection or the
repository-configured admitted default. If neither exists, keep the admitted coordinator route as the
operational default. Override that default only with a current representative repository evaluation
for the same task shape, tools, data class, and success measure. A default or eval MUST NOT override
data admission, local-execution, authority, writer-lease, or review gates.

## Operating topology

### Coordinator

The coordinator MUST maintain a task ledger containing current intent, non-goals, authority
boundaries, acceptance criteria, risk classification, dependency state, writer lease, dispatched
packets, receipts, reviews, and unresolved decisions. Before dispatch and after any context
compaction or handoff, it MUST re-read the applicable instructions and ledger.

Use an existing authorized durable surface for the ledger: the harness plan/goal, an issue or PR
record, a checked-in task document when documentation is in scope, or an explicit handoff. Do not
create commits, GitHub comments, or external records without the authority already required for those
actions. Before ending or transferring a long-running task, externalize the current ledger to an
authorized surface so it does not exist only in one model session.

The coordinator selects routes, reconciles evidence against callers/tests/the real artifact, owns
user updates, and stops when new authority is required. It MAY delegate the writer lease to a
specialist but remains accountable for verification.

If the coordinator implements directly, it also occupies the worker role for that bounded packet and
MUST produce the same author receipt before moving work to `verified`. That self-receipt records work;
it is not independent review and cannot satisfy a different-family review gate.

### Supervisor

Use a supervisor when a task has a background-capable session, long-running process, hosted CI wait,
or worker set that can be observed independently. If the environment has no independent supervision
mechanism, the coordinator performs the same checks; do not invent a pretend supervisor.

The supervisor MUST remain read-only for product code and MUST NOT expand scope or authority. It
registers each dispatched task ID, route, writer lease if any, deadline, and required checks. Routine
progress, unchanged state, and successful bounded retries stay in the background. Escalate only when:

- a decision or new permission is required;
- a retry, cost, or time budget is exhausted;
- a required route is denied, unavailable, or timed out;
- reviewers materially disagree;
- instruction/context drift is detected;
- a safety invariant or required check fails; or
- the requested outcome is complete.

A retry with write scope MUST first terminate the prior writer process, confirm that its session can
no longer edit, record the writer lease as released, and inspect the checkout before assigning a new
writer. The supervisor MUST NOT dispatch two writers to one checkout.

### Specialist leads and workers

Specialist leads own bounded domains such as architecture, implementation, UI, security, operations,
research, or delivery. They inherit every route-admission, data, authority, writer, and receipt rule in
this contract. They MUST re-anchor to their fixed packet at each durable event and MUST NOT broaden
worker scope or provider access.

Workers receive narrow discovery, candidate, test, or review tasks. A worker is read-only unless its
packet grants the writer lease. Candidate implementations require isolated checkouts and a declared
integration owner.

When the user explicitly requests every available model, the coordinator MUST inventory the currently
installed and admitted families and give each safe, relevant family a distinct candidate or review
lens. It MUST record unavailable, denied, timed-out, duplicate-family, or irrelevant routes. It MUST
NOT commission interchangeable opinions merely to increase the model count.

## Lifecycle states

Track these explicit states in the task ledger:

- Route: `proposed -> admitted | denied | unavailable`.
- Work: `packeted -> dispatched -> running -> receipt-received -> verified -> accepted | rejected`.
- Exceptional work: `running -> timed-out | failed | cancelled | blocked-authority`.
- Candidate import: `candidate-ready -> import-pending -> verifying -> accepted | reverted`.
- Review: `pending -> passed | dissent | unsatisfied`.

Every terminal transition needs a receipt. `dissent`, `unsatisfied`, `blocked-authority`, required-route
failure, and failed safety checks trigger coordinator escalation. A specialist-spawned worker MUST be
registered with the supervisor or coordinator before entering `dispatched`.

## Dispatch and route admission

Before dispatch, create a task packet with:

- task ID, objective, and non-goals;
- risk classification and triggering facts;
- repository path, base commit, and fixed artifact snapshot fingerprint;
- relevant contracts, callers, and every applicable instruction file or skill reference;
- permitted read/write paths, external actions, and designated writer lease;
- acceptance criteria and commands to run;
- data classification and repository-approved provider route;
- deadline, bounded retry condition, and required return shape.

An uncommitted candidate needs both its base commit and a content-addressed artifact manifest or
snapshot that covers every in-scope committed, staged, unstaged, and untracked file. Record the
inclusion method and SHA-256. A normal working-tree diff may omit untracked files; `HEAD` or a diff
alone is not a fixed review target.

Before a provider-backed CLI enters `admitted`, record:

- CLI and version;
- actual provider, model ID, family, mode, and reasoning level;
- proof that the execution mode is locally launched rather than a cloud coding agent;
- account/data-route retention, training-use, and ZDR facts from authoritative sources;
- packet data class and exact permitted artifact;
- read-only or writer permissions, writer lease if any, and timeout; and
- the representative eval used for a non-default selection, if one exists.

Repository data-route rules win. Provider-backed engineering CLIs are external engineering routes,
not product inference routes. By default, prompts contain only public source, synthetic fixtures, or
approved de-identified material. Never send secrets or credentials. Client, production, health,
financial, legal-matter, or personal data requires a prior scoped approval naming the approver,
artifact/data class, provider, model/account, purpose, retention terms, and expiry. If the packet
cannot be sanitized or admitted, enter `denied` or `blocked-authority`; never substitute a provider.

Only locally launched interactive/headless modes acting on the controlled checkout are eligible.
Hosted/background workspace delegation, provider-managed VMs, remote PR agents, cloud sessions, and
any tool that can push or write outside the local checkout are prohibited.

### Grok approve-mode invariant

Every direct Grok CLI launch MUST use the installed `lee-grok` wrapper. The wrapper injects
`--always-approve` and rejects `--permission-mode` and a caller-supplied `--always-approve`. Agents
MUST NOT call the underlying `grok` binary directly. The user-level Grok configuration MUST also
contain exactly this setting:

```toml
[ui]
permission_mode = "always-approve"
```

Before admitting a Grok route in a new environment, run the installed
`lee-engineering/scripts/sync_grok_harness.py verify --json`. A missing wrapper, configuration drift,
or skill digest mismatch makes the route `unavailable`; do not improvise another permission mode.
In particular, Grok's `--permission-mode acceptEdits` is forbidden: Grok CLI 1.0.5 returned
`stopReason: cancelled` before its first edit tool call under that mode, while the same fixed probe
completed with `--always-approve`.

For a fixed-artifact, read-only Grok review, use `lee-grok-review`. It pins Grok 4.6 at low reasoning,
keeps approve mode active, disables memory, planning, subagents, web access, and built-in tools, limits
the run to one turn, and emits streaming Messages JSON. Split a large artifact into named immutable
slices with the whole-artifact fingerprint in every packet. Do not use a short watchdog around
non-streaming `json`: Grok 4.6 can stream reasoning for minutes on a large patch before producing its
final result, which is active inference rather than quota exhaustion or a permission deadlock. Use
`lee-grok` directly when a Grok worker needs tools or deeper reasoning.

Every Cursor Agent route backed by Grok MUST use the installed `lee-cursor-grok` wrapper. It pins
Grok 4.6 and injects `--force`, the Cursor approve-mode equivalent, while rejecting caller-supplied
model, mode, force, yolo, and auto-review flags. Cursor-backed Grok remains a distinct harness
admission and MUST pass a fixed one-edit tool probe before authoring. A direct Grok pass does not
prove the Cursor tool bridge.

Approve mode changes tool-confirmation behavior only. It MUST NOT expand the packet's writer lease,
filesystem scope, data route, GitHub authority, network authority, or external side-effect authority.
Use sandboxing, tool denials, a bounded checkout, and the task packet to enforce those boundaries.
For installation and cross-environment verification, read
[`grok-harness.md`](grok-harness.md).

## Receipts and handoffs

Every worker and specialist returns a receipt containing:

- task ID, exact CLI/version/provider/model/family/mode, and whether it counted as independent;
- base, artifact-snapshot inclusion method, and fingerprint inspected;
- actual data route and retention terms applied;
- files or contracts changed, if authorized;
- commands/checks run and exact results;
- findings, corrections, uncertainty, and material dissent;
- lifecycle terminal state and writer-lease release state; and
- next decision, if any.

The coordinator MUST verify a candidate against its receipt before importing it. Commits, fixed patch
fingerprints, CI transitions, review findings, and persisted receipts are durable events. Prefer them
over status chatter.

## Independent review and completion

Merge-critical, security-sensitive, high-risk, or contested work MUST receive fixed-artifact review
from at least one admitted different model family. Give reviewers the same intent, fixed artifact,
acceptance criteria, and evidence. The author model's self-review cannot satisfy this gate.

Review independence counts only when the resolved underlying family differs from the author's. If no
admitted different-family route completes, set review to `unsatisfied`, stop publication/merge, and
escalate to the user. A timeout or unavailable route is not approval and does not authorize a less
private route.

Reconcile disagreement with repository instructions, callers, primary documentation, tests, and the
real artifact. Confidence, reputation, and majority vote do not decide correctness. Stop when the
required evidence is complete; additional agents must contribute a distinct candidate, risk lens, or
verification path.

## Repository evaluation record

Promote or demote a route only after repeated repository tasks show a material difference in
correctness, completeness, corrections, latency, or cost. Record the task packet, fixed artifact,
exact tool/model/effort, result, checks, corrections, and lead judgment. Keep negative results and
re-run after material model, CLI, account, or repository changes.
