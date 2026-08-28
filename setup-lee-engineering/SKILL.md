---
name: setup-lee-engineering
description: Set up the agent skills collection for whatever harness you are in. Links the skills into every harness from one copy, scans which models the account can actually reach, assigns them to engineering roles, and writes the harness's own routing config. Use for /setup-lee-engineering, "set up lee-engineering", "which models do I have", "scan my routes", "configure my model routing", or before any multi-model dispatch.
---

# Setup

One command does all three. Run it; do not predict its output.

```bash
bin/agent-setup            # link skills, scan models, assign roles, write harness config
```

`--dry-run` writes nothing. `--status` reports state without probing. The steps are also separate:

```bash
bin/agent-skills link      # one copy of the skills, linked into every harness
bin/agent-routes scan      # which models this account can actually reach
bin/agent-roles apply      # assign them to roles, and write the harness config
```

Everything lives in the skills-collection clone. Find it from any harness:

```bash
readlink -f ~/.agents/skills/setup-lee-engineering
```

Report back: which roots were linked and whether any had drifted, which harness was detected and
how, how many routes came from the harness versus a vendor CLI, the role assignment, and any gap.

## 1. One copy, many harnesses

`link` makes the clone the only copy on disk and symlinks it into every harness skill root present:
`~/.agents/skills` (the cross-agent convention, read by Cursor, Codex and Gemini CLI),
`~/.claude/skills` (Claude Code does not read the convention path), plus Cursor, Codex, Grok, Gemini,
Factory, Droid and T3 roots when those harnesses exist.

`status` flags a root that drifted into a copy. `prune` clears the dangling links a renamed skill
leaves behind.

`link` also makes `CLAUDE.md` a symlink to `AGENTS.md`, so Claude Code sees the file it looks for
while there is still only one file to edit. Never edit `CLAUDE.md`; edit `AGENTS.md`. If the two
already differ, the link is refused rather than clobbering either.

Do not install this collection as a plugin. Cursor and Claude Code both cache a plugin per harness,
which is the duplication this avoids.

## 2. Scan what you can reach

`scan` probes the harness you are in first, then any vendor CLI or manifest on the machine, and
writes `~/.agents/routes.json`. Each route carries:

| Field | Meaning |
| --- | --- |
| `sourceKind` | `harness` for the one you are in, `cli-fallback` for anything else |
| `family` | model lineage from the model ID: what makes a review independent |
| `pool` | the provider account meter: what makes scheduling honest |
| `preferOver` | set when a CLI route duplicates a family the harness already reaches |

Read `status` per source before concluding anything: `ok`, `empty`, `no-api` (the tool publishes no
model list), `failed`, `timeout`, `unavailable`. **A failure is not an absence.**

Some harnesses publish no model list at all. The scan then emits one **live-session** route for the
model you are already talking to, with `family: unknown`. Keep working on it. Do not leave a working
session for a CLI just because the CLI produced a catalog.

## 3. Assign roles and write the config

`agent-roles assign` picks a route per role and writes `~/.agents/routing.json` and
`~/.agents/routing.md`. `agent-roles apply` does that and also writes the current harness's own role
configuration when it has one.

| Role | Used for |
| --- | --- |
| `plan` | architecture, design, hard judgment |
| `implement` | writing and changing code |
| `review` | independent review; forced into a different family from `implement` |
| `scout` | cheap exploration and summarising |
| `verify` | checking claims; also a different family from `implement` |

Selection uses only what the scan carries plus vendor naming convention: harness before CLI, healthy
pool before constrained, reasoning support, tier words (`nano`/`haiku`/`flash` small,
`opus`/`pro`/`max` large), and version parsed from the model ID. Price is deliberately not a
capability signal, because a legacy flagship is often the priciest entry in the catalog and the worst
choice.

Two rules hold everywhere:

- **Never a model you cannot reach.** Only selectors present in the scan are ever written. A role
  pointing at an unreachable model breaks every delegation that reads it.
- **Override layer, inline fallbacks.** A role with no assignment keeps whatever default the skill
  already uses, so nothing breaks when the file is missing or stale.

### Harness adapters

`apply` writes the harness's native config where one exists:

- **Oh My Pi (`omp`)** — merges into `modelRoles` and `task.agentModelOverrides` through
  `omp config set`, the supported mutation path. Roles it does not manage are preserved, the previous
  values are saved to `~/.agents/backups/`, and the thinking level is chosen from the levels each
  model actually supports: highest for a capability role, lowest for a cheap one.
- **Any other harness** — no native role config, so the neutral `routing.json` is the contract and
  skills read it directly. That is reported, not treated as a failure.

### Pinning a role yourself

The ranking is a heuristic and will sometimes be wrong. Pin a role in
`~/.agents/roles.overrides.json` and it wins on every re-run:

```json
{ "review": "<a selector present in the scan>" }
```

A pin naming a model the scan did not find is ignored and reported.

## Re-run when

- a dispatch fails with an unknown model;
- credentials, accounts, subscriptions, or the harness change;
- a provider returns a quota, billing, or authentication error;
- you add a harness or a CLI.

Re-running is idempotent: `link` is a no-op when everything is linked, and `assign` overwrites the
whole routing file so there is no accumulated state.

## When nothing is found

With no harness detected and no CLI listing models, report what was probed and stop. Do not fall back
to assumption. If a harness was detected you always have at least the live-session route.

Adding a harness or CLI is one entry in `PROBES` in `bin/agent-routes`. Add it there rather than
working around it in prose.
