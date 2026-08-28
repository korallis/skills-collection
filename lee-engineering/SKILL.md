---
name: lee-engineering
description: Global TypeScript-first engineering router. Use whenever planning, designing, building, implementing, refactoring, debugging, reviewing, or documenting software. Selects the smallest relevant specialist skills, routes work across whatever models this account can actually reach, verifies against the real artifact, and delivers through GitHub.
---

# Lee Engineering

Default entry point for software work. Read
[`references/principles.md`](references/principles.md) for non-trivial planning, architecture,
implementation, or review.

## Establish scope

1. Read the repository's instructions, manifests, relevant source, tests, and current Git state.
2. Treat repository-local product, language, and verification rules as authoritative.
3. Prefer TypeScript for new applications, services, packages, scripts, and developer tooling when
   the repository and user have not selected another language. Do not rewrite a healthy
   non-TypeScript codebase merely to satisfy this preference.
4. Keep planning and implementation inside the user's authorization. Skill activation never grants
   permission to push, open or merge a PR, deploy, message people, or mutate unrelated external state.
5. Do not route work to cloud coding agents.

## Know your routes before you dispatch

Never assume which models or CLIs exist. Scan, then use the roles that scan produced.

```bash
bin/agent-routes scan && bin/agent-roles apply   # or the setup-lee-engineering skill
```

`~/.agents/routing.json` names a model per role: `plan`, `implement`, `review`, `scout`, `verify`.
Dispatch against those roles rather than naming a model. `review` and `verify` are guaranteed to sit
in a different model family from `implement`, which is what makes a review independent.

A role with no assignment keeps whatever default you would otherwise use, so a missing or stale
routing file never breaks a dispatch. `~/.agents/routes.json` holds the full scan when you need the
detail: families, capacity pools, and per-source status.

Re-scan when a dispatch fails with an unknown model, when credentials or accounts change, or when the
scan predates this session.

Some harnesses publish no model list. The scan then emits one live-session route for the model you
are already on: keep working there rather than leaving for a vendor CLI. A CLI is a fallback for a
family or capability the harness cannot provide, never a replacement for a working session.
`status: failed` or `timeout` means unknown, never absence.

If no scan is possible at all, say so and continue single-agent on the current model.

Full routing contract, including the capacity and review rules: [`references/routing.md`](references/routing.md).

## Route the work

Load only the skills that materially help the current task:

- A new system or high-risk cross-cutting plan: `architect`. A focused API, module boundary, or
  component design: `codebase-design`. Existing structural debt or architecture refactoring:
  `improve-codebase-architecture`. Use one of these by default, not all three; add `domain-modeling`
  when domain concepts or state transitions are central.
- An under-specified product or architecture decision: `grilling`; use `grill-with-docs` when the
  outcome should also update a glossary or architecture decision record.
- A settled plan that needs independently verifiable GitHub work units: `to-tickets`, while keeping
  the repository's existing tracker and source-of-work rules authoritative.
- TypeScript or TSX implementation and review: `typescript-best-practices`.
- Writing, placing, or reviewing code in any language: `clean-code`. Adding a dependency, layer, or
  module boundary: `clean-architecture`. Creating an app, module, package, workspace, or folder
  tree: `scaffolding`.
- New behavior or a defect fix: `tdd`; for an unknown failure, start with `diagnosing-bugs`.
- Merge conflicts: `resolving-merge-conflicts`.
- Large work with independent slices: `waves`.
- Competing viable designs or implementations: `arena`.
- Wide or risky changes: `blast-radius` before declaring completion.
- Contested, security-sensitive, or merge-critical review: `interrogate`.
- Ordinary code review: `code-review`.
- External facts, library behaviour, API semantics, or an error message: `research`.
- Agent instructions and technical prose: `writing-for-agents` and `technical-writing`.
- Branch, pull-request, check, or merge work: `github-delivery`.

Do not invoke every skill mechanically. Prefer the smallest combination that improves the result.

## Build and verify

1. Make data structures, contracts, and module boundaries explicit before adding orchestration.
2. Implement the smallest coherent slice that proves the design through a real caller or workflow.
3. Test at the closest useful layer, then run the repository's required checks.
4. Inspect the changed artifact and its callers, not just command exit codes.
5. For user-visible behavior, verify the real user path when the repository supports it.
6. Before handoff, state what changed, what was verified, remaining risk, and any action requiring
   separate authorization.
