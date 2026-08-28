---
name: setup-lee-engineering
description: Install this skills collection into every harness on this machine and discover which models the account can actually reach. Use for /setup-lee-engineering, "set up lee-engineering", "which models do I have", "scan my routes", or before any multi-model dispatch.
---

# Setup

Two jobs: put the skills in one place every harness reads, then find out what models this account
can actually reach. Both are scripts. Run them; do not predict their output.

Everything lives in the skills-collection clone. Find it, and work from there:

```bash
ls ~/.agents/skills/setup-lee-engineering   # a symlink points at the clone
readlink -f ~/.agents/skills/setup-lee-engineering
```

## 1. One copy, many harnesses

```bash
bin/agent-skills status     # what each harness root points at
bin/agent-skills link       # symlink every skill into every harness root found
```

The clone is the only copy on disk. Every harness skill root becomes a symlink into it, so editing a
skill changes it everywhere at once and no root can drift.

`status` reports `copy` or `linked-elsewhere` when a root has drifted. That is the failure this
replaces: an agent reading a stale duplicate while you edit the original.

Do not install this collection as a Cursor or Claude Code plugin. Plugin installs are per-harness
caches, which is the duplication this avoids.

## 2. Scan the routes

```bash
bin/agent-routes scan       # probe and write ~/.agents/routes.json
bin/agent-routes show       # reprint the last scan without probing
```

The scan answers one question: **which models can this account actually reach right now.** It
probes the harness you are in first, then any vendor CLI on the machine, and writes every result to
`~/.agents/routes.json`.

Each route carries:

| Field | Meaning |
| --- | --- |
| `sourceKind` | `harness` for the harness you are in, `cli-fallback` for a vendor CLI |
| `family` | model lineage derived from the model ID: what makes a review independent |
| `pool` | the provider account meter that can stop it: what makes scheduling honest |
| `preferOver` | set when a CLI route duplicates a family the harness already reaches |

## Read the scan, not your memory

- `routes.json` is the answer to "what can I run this on". An installed binary, a
  vendor documentation table, a model name in a config file, and a remembered environment are all
  inadmissible.
- **A vendor CLI is a fallback.** When `preferOver` is set, the harness already reaches that family;
  going out to the CLI adds a second data route and a second draw on the same meter and buys
  nothing. Use a CLI only for a family or capability the harness genuinely cannot provide.
- **Family and pool are independent.** One provider account often serves several families, and one
  family is often reachable from several accounts. Check `families` in the scan before concluding a
  model family is unavailable.
- A pool with no usage numbers is `unknown`, not free. Send one small packet, then re-scan.

## Re-scan when

- a dispatch fails with an unknown model;
- credentials, accounts, subscriptions, or the harness change;
- the scan predates the current session;
- a provider returns a quota, billing, or authentication error.

## When your harness publishes no model list

Claude Code, Codex, Gemini CLI and opencode do not publish one. That is a fact about the tool, not
evidence you have no models: you are demonstrably talking to one right now.

In that case the scan records the source as `status: no-api` and adds a single **live-session**
route with `selector: <live session>` and `family: unknown`. Read it as: keep working on the model
you are already on. Do not leave a working session to spawn a vendor CLI merely because the CLI is
the only thing that produced a catalog.

`family: unknown` means the session's model cannot be named, so it cannot satisfy a review gate that
requires a *different* family. For that gate, and only that gate, a CLI route is a legitimate
fallback.

Distinguish the `status` values before concluding anything:

| Status | Meaning |
| --- | --- |
| `ok` | routes were listed |
| `no-api` | the tool publishes no model list; absence of data, not absence of models |
| `empty` | the tool listed nothing |
| `failed` | the probe errored; treat as unknown, not as absence |
| `timeout` | the probe hung; treat as unknown, not as absence |
| `unavailable` | detected as the current harness, but its binary is not on `PATH` |

## When the scan genuinely finds nothing

With no harness detected and no CLI listing models, report what was probed and stop. Do not fall
back to assumption. If a harness was detected, you always have at least the live-session route.

Adding support for a harness or CLI is one entry in `PROBES` in `bin/agent-routes`. If a harness is
missing, add it there rather than working around it in prose.
