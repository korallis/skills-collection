# Routing work across models

Read after `bin/agent-routes scan` has written `~/.agents/routes.json`. That file says what is
reachable. This file says what to do with it.

Repository instructions and explicit user authority override everything here.

## When this applies

A task is non-trivial when it changes behavior, a public or inter-module contract, architecture,
security, privacy, CI, deployment, durable state, or more than one independently owned module. A
mechanical single-file change with no behavioral effect stays single-agent.

Classify risk before dispatch as one or more of `ordinary`, `high-risk`, `security-sensitive`, or
`merge-critical`, and record what triggered it. Deployment, release and rollback, ingress or
service-manager configuration, CI promotion, authentication, durable-state transitions, data
migration, irreversible operations, and external side effects are `high-risk` by default.

## Reading the scan

Two fields decide everything, and they are independent:

- **`family`** is the model lineage, derived from the model ID. It decides review independence. A
  reviewer in the author's family is not an independent reviewer, whichever harness ran it.
- **`pool`** is the provider account meter. It decides scheduling. Exhausting a pool removes every
  route drawing on it, regardless of family.

One account commonly serves several families, and one family is commonly reachable from several
accounts. So:

- Two routes in different families can share one meter. Reserve review capacity against the **pool**,
  not the family name.
- Two routes in one family can sit in different meters. Before declaring a family unavailable, check
  `families` in the scan for another pool that reaches it.
- `family: unknown` never satisfies a review gate. An unprovable family is not a different family.

## Prefer the harness

`sourceKind: harness` routes are the default. A `cli-fallback` route with `preferOver` set duplicates
a family the harness already reaches: taking it adds a data route and a second draw on the same meter
and buys nothing.

Several harnesses publish no model list at all. There the scan records `status: no-api` and emits one
**live-session** route: the model you are already talking to, with `family: unknown`. Stay on it. A
CLI listing many models does not make those models better than the one already answering you, and an
empty harness catalog is missing data, not a missing model. Read `status` before concluding anything:
`failed` and `timeout` mean unknown, never absence.

Reach for a CLI fallback only for a family or capability the harness genuinely cannot provide: a
family absent from the scan, a **different** family for a review gate the live-session route cannot
satisfy because its own family is unknown, or a second concurrent writer process. A vendor
preference is not a capability gap. See [`fallback-clis.md`](fallback-clis.md) before launching one.

Never route work to a cloud coding agent: a hosted task, provider-managed workspace or VM, remote PR
agent, or anything that can write outside the local checkout.

## Roles

- **Coordinator** — the user-facing context. Owns intent, authority, acceptance criteria, dependency
  order, and final judgment. Keeps the ledger below.
- **Specialist** — a bounded domain session accountable for one result.
- **Worker** — a short-lived session with a fixed packet and a required return shape.
- **Writer lease** — exclusive permission for one process to edit one checkout. A branch may have
  sequential writers. A checkout must never have two at once.

If the coordinator implements directly it also occupies the worker role and owes the same receipt.
That self-receipt records work; it is not independent review.

## The ledger

Keep current intent, non-goals, authority boundaries, acceptance criteria, risk classification, the
scan timestamp, the writer lease, dispatched packets, receipts, reviews, and open decisions. Put it
on an authorized durable surface: the harness plan, an issue or PR, or a checked-in task document
when documentation is in scope. Do not create commits or comments you lack authority for. Before
ending a long task, externalize the ledger so it does not live only in one session.

## Dispatch

A packet carries: objective and non-goals; risk classification; repository path, base commit, and a
content-addressed fingerprint of the exact artifact; relevant contracts and callers; permitted read
and write paths; the writer lease if granted; acceptance criteria and the commands to run; the data
class; the chosen `routeId` from the scan; and a deadline.

An uncommitted candidate needs its base commit **and** a manifest covering every in-scope committed,
staged, unstaged, and untracked file. A working-tree diff can omit untracked files, so `HEAD` or a
diff alone is not a fixed review target.

Data rules: by default a prompt carries only public source, synthetic fixtures, or approved
de-identified material. Never send secrets or credentials. Client, production, health, financial,
legal-matter, or personal data needs prior scoped approval naming the approver, data class, provider,
purpose, retention terms, and expiry. Retention differs between a vendor's API and the same vendor's
subscription surface, and an aggregator route inherits the aggregator's terms. If a packet cannot be
sanitized, stop; never quietly substitute a provider.

## Scheduling against capacity

`pools` in the scan carries usage per meter. Apply hard gates first — authority, data class, task
fit, writer lease — then schedule what remains:

1. Drop exhausted and blocked pools.
2. Reserve review-sized headroom for every independent-review gate you already know about, in a pool
   that can serve a non-author family. Re-check that reserve after each assignment: assignments
   consume pools, and the last eligible pool can disappear mid-wave.
3. Spend the rest on the best task-fit route, pacing each pool against its own reset rather than
   spreading traffic evenly.
4. A pool with `usedFraction: null` is unmetered, not free. Send one small packet, then re-scan.
5. When no pool can hold the reserve, which is normal where no CLI exposes a meter, record it
   unplaced and run required review work before discretionary work. An unplaceable reserve limits
   duplicate work; it never blocks assignment.

A quota, billing, or authentication error invalidates that pool immediately. Re-scan before reusing
it. A reset time passing makes the old scan stale; it does not prove the route is back.

## Receipts

Every worker returns: the packet ID and `routeId`; **the model the run actually resolved to, read
back from the result rather than the request**; the base and artifact fingerprint inspected; files or
contracts changed; commands run and their exact results; findings, corrections, and dissent; and the
writer-lease release state.

Read the model back because pins are advisory in several harnesses. A silent substitution to a
compatible model can quietly make a reviewer share the author's family and collapse the review gate.

Verify a candidate against its receipt before importing it. Commits, fixed fingerprints, CI
transitions, and persisted receipts are durable events; prefer them to status chatter.

## Independent review

Merge-critical, security-sensitive, high-risk, or contested work needs fixed-artifact review from at
least one route in a different family from the author. Give every reviewer the same intent, the same
fixed artifact, the same acceptance criteria, and the same evidence.

Exhaustion is not a dead end until you have checked, in order: another pool serving that family, any
other non-author family in the scan, then a CLI fallback.

If no different-family route completes, or a receipt cannot prove which family answered, the review
is unsatisfied. Stop publication and escalate. A timeout is not an approval, and it does not justify
a less private route.

Reconcile disagreement against repository instructions, callers, primary documentation, tests, and
the real artifact. Confidence and majority vote do not decide correctness. Stop when the evidence is
complete; another agent must add a distinct candidate, risk lens, or verification path to be worth
running.
