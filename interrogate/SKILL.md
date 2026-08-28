---
name: interrogate
description: Independent local multi-model review for contested, security-sensitive, high-risk, or merge-critical plans and changes. Use when one reviewer is insufficient. Gives reviewers the same intent and rubric, aggregates consensus and disagreements, and applies lead judgment without pretending model diversity.
---

# Interrogate

Run independent reviews, then make one accountable decision.

## Prepare the packet

Provide every reviewer the same task intent, repository constraints, relevant diff or plan, and
verification evidence. Ask each to return only actionable findings with severity, location, causal
reasoning, and a concrete fix or proof request.

Use this rubric:

- correctness and contract preservation;
- security, privacy, and authorization boundaries;
- state, concurrency, retry, and failure behavior;
- TypeScript type safety and boundary validation where applicable;
- architecture, maintainability, and unnecessary complexity;
- test strength and real-artifact verification;
- repository-specific acceptance and delivery rules.

## Consult independently

Dispatch reviewers as harness-native subagents, read-only. For model choice, read
`~/.agents/routing.json` (written by the `setup-lee-engineering` skill): reviewers run on the
`review` and `verify` roles, which setup guarantees sit in a different model family from the
author's. No routing file, or a role with no assignment, means review on the current model and say
so — same-model review is a weaker gate, not a fake independent one. A separately installed model
CLI is an optional extra reviewer, never a requirement.

Never simulate or label a reviewer as a model that did not actually run; read the model back from
the run result, not from the request. Keep reviewers isolated until their first verdict, and do not
let review agents edit, push, merge, deploy, or contact people.

## Aggregate with lead judgment

Deduplicate findings and label:

- **Consensus:** independently raised by multiple reviewers.
- **Lone finding:** raised once but supported by evidence.
- **Disagreement:** incompatible conclusions that require resolution.

The lead agent reads the underlying code or artifact and classifies each item as **Act on**,
**Consider**, **Noted**, or **Dismissed**, with a short evidence-based reason. Reviewer votes are
signals, not authority. Do not apply proposed fixes unless implementation is within the user's
request. End with the blocking findings, non-blocking improvements, dismissed noise, and verification
needed to close the review.
