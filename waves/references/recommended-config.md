# Recommended harness requirements

Use this as a starting point for the `waves` workflow. The runner MUST
satisfy the capabilities below. How each harness names tools, config
files, or spawn APIs is its own concern; this skill does not require a
particular vendor config path.

Dispatch each worker the way the current harness dispatches workers: a
bounded worker with a fixed packet and a required return shape. The
packet includes objective, non-goals, slice, permitted paths, acceptance,
the chosen `routeId` from the scan, and the required return shape from
[handoff-format.md](handoff-format.md). Track the plan on the harness
plan/todo surface.

## Parallel workers

The runner MUST support parallel workers with bounded concurrency.

- Respect the harness worker-concurrency cap. If the cap is unknown,
  batch 3–8 workers.
- Recursion is off by default: workers MUST NOT spawn workers.
- Manager-driven sequential waves (a second or third wave at the same
  depth, after the previous wave returns) are encouraged.
- For row-shaped work, use the harness batch/CSV spawn when it exists;
  otherwise spawn one worker per row.

## Per-worker route selection

Pick each worker's model/route from `~/.agents/routes.json`, written by
`bin/agent-routes scan`. Prefer entries with `sourceKind: harness`.

- `family` decides review independence (use a different family from the
  author when independence matters).
- `pool` decides scheduling.
- A vendor CLI is a fallback only for a family or capability the harness
  cannot provide.

## Return contract

Every worker MUST return the structured handoff in
[handoff-format.md](handoff-format.md). Reject or re-run a worker that
omits coverage, confidence, or concrete sources when the packet required
them.

## Tool restrictions

- Explorers, reviewers, and verifiers: read-only. They MUST NOT edit
  files.
- Implementation workers: write only inside the owned slice (explicit
  files or modules). They MUST NOT revert changes they did not make or
  touch unrelated paths.
- Research workers: read-only unless the packet explicitly assigns
  edits.

## Web and docs access

When a slice depends on current APIs, versions, or live docs, the worker
MUST have web/docs access (harness web search, docs MCP, or equivalent).
Cite source URLs and call out date-sensitive or uncertain details.

## Isolated writes

Parallel writes MUST use isolated git worktrees or disjoint path
ownership. Do not point two writers at the same files.

## Role defaults

Map roles to routes from the scan. Do not hardcode vendor model slugs.

| Role | Route to pick |
| --- | --- |
| Manager / coordinator | High-capability harness route |
| Scouting / read-heavy | Cheaper/faster harness route |
| Research | Capable route with live web/docs access |
| Implementation | Capable coding route |
| Reviewer / verifier | Capable route; prefer a different `family` from the author when independence matters |

## Verification defaults

Recommended acceptance bars:

- Pre-fan-out: counts, slice bounds, partition-sum, gaps/duplicates.
- Every handoff: evidence resolves, scope matches, confidence labels
  preserved.
- High-stakes claims: a verifier worker (or batch verifier pass).
- Code edits: tests or type checks plus a diff review.
- Generated files: parser/schema/validator where possible.
- Final response: keep `verified`, `single-sourced`, and `unverified`
  distinct.

## Skill install

Skill install is harness-specific. This collection is linked by
`bin/agent-skills link` into each harness skill root. Do not assume a
single vendor skill directory.

---

## Appendix: Codex configuration examples (optional, one harness)

The rest of this file is **Codex syntax for one harness**, not the skill
requirement. Keep it only if you are running on Codex. TOML under
`~/.codex/config.toml` or `.codex/config.toml`, `codex exec`, GPT-5.6
slugs, `agents.max_threads`, custom agent TOML, `spawn_agents_on_csv`,
and `approvals_reviewer` are Codex-only.

### Example: Codex native-delegation caution (GPT-5.6)

On GPT-5.6 Sol/Terra (the V2 multi-agent runtime), the primary steering
surface is **prompt and skill text, not config**: delegation triggers on
direct asks and "applicable AGENTS.md or skill instructions," and per-spawn
model/effort routing is honored when explicitly requested the same way.
Custom TOML role routing has been unreliable on V2 (roles resolving to null,
model/sandbox pins ignored -- openai/codex #31814, #32587, #32782; per-spawn
overrides restored in 0.145+ as explicit-only). Practical stance:

- Everything below still works for V1 surfaces, `codex exec` fleets, and as
  declarative documentation of your intended roles -- but on 5.6 V2, treat
  TOML as optional tuning and **inline each role's instructions and intended
  model/effort in the worker prompt** (the skill's default pattern).
- Do not set `ultra` for wave runs: it flips delegation to proactive (spawns
  outside your manifest) and its children inherit ultra.
- V2 ignores `agents.max_depth`; the binding limit is concurrent agent slots
  (4 including the manager by default, `agents.max_threads + 1` when set --
  keeping `max_threads = 6` below yields 7 slots).
- Luna is still V1: Sol/Terra parents cannot spawn Luna children. Terra is
  the cheap tier for spawned workers; use Luna from the main thread or
  `codex exec`.
- After each Codex release, re-verify which spawn parameters
  (`agent_type`, `model`, `reasoning_effort`, fork behavior) are actually
  exposed before relying on them -- this surface has changed three times in
  July 2026 alone.

### Example: Codex default manager/worker setup

```toml
# Manager default. gpt-5.6 is the alias for gpt-5.6-sol (flagship); route
# cheaper tiers (gpt-5.6-terra, gpt-5.6-luna) per worker role and scale
# depth with reasoning effort. Orchestration benefits from extra-high reasoning.
model = "gpt-5.6"
model_reasoning_effort = "xhigh"

[features]
# multi_agent enables the subagent collaboration tools. In current Codex it is
# Stable and defaults to true, so this line is optional -- keep it for clarity.
multi_agent = true

[agents]
# Current Codex default is 6 when unset. Keep it explicit for this workflow.
max_threads = 6

# Current default is 1: root can spawn direct children, children cannot recurse.
# This caps recursion only; manager-driven second/third waves at depth 1 are
# unaffected and encouraged (see SKILL "Step 4 - Second Waves").
max_depth = 1

# Default per-worker timeout for spawn_agents_on_csv jobs.
job_max_runtime_seconds = 1800
```

Recommended defaults (GPT-5.6 family, GA 2026-07-09; `gpt-5.6` = Sol flagship,
`gpt-5.6-terra` = balanced/cheaper, `gpt-5.6-luna` = fastest/cheapest):

- Manager/orchestrator: `gpt-5.6` with `xhigh` effort for complex problem
  solving, orchestration, deep thinking between steps, and synthesis before
  fan-out. Escalate to `max` for the hardest quality-first passes; use
  `medium` only for simpler manager passes.
- Read-heavy / scouting / decomposition workers: `gpt-5.6-terra` with `low`
  effort for the fast reads, greps, counting, scans, and doc lookups that
  reduce entropy before you slice (this matches official Codex guidance for
  lighter subagent work). `gpt-5.6-luna` is even cheaper for short-context
  slices, but never give Luna long-context reads -- its recall collapses on
  256K+ contexts (OpenAI MRCR tables). `gpt-5.3-codex-spark` (research
  preview) is the near-instant text-only option; `gpt-5.4-mini` remains an
  older lightweight fallback.
- Research/all-around workers: `gpt-5.6-terra` with `medium` effort (step up
  to `gpt-5.6` when the stream is ambiguous or high-stakes).
- Implementation workers: `gpt-5.6` with `high` effort.
- Reviewer/security/verifier workers: `gpt-5.6` with `high` effort.
- `max_threads`: keep `6` as the default. Raise only for simple read-heavy work
  on a machine and rate-limit budget that can handle it.
- `max_depth`: keep `1`. Raise to `2` only for deliberate recursive delegation
  with strict instructions and budget awareness.

Effort field names, ladder, and speed tier:

- The documented effort ladder is `none`, `minimal`, `low`, `medium`, `high`,
  `xhigh`, `max` (model-dependent at both ends). `ultra` is a Codex product
  setting, not a config value: it runs `max` with proactive multi-agent (~4
  parallel agents, roughly 3-4x single-agent cost) -- reserve it for a single
  unresolved high-stakes slice, if ever.
- The live per-spawn field is `reasoning_effort`; the config / custom-agent TOML
  key is `model_reasoning_effort`. Set the effort on each spawned worker, not
  only in config. (V2 exposes per-spawn `model`/`reasoning_effort` overrides
  only when `multi_agent_v2.expose_spawn_agent_model_overrides` is enabled;
  custom agent TOML always works.)
- Context note: Codex clients currently treat GPT-5.6 context as 272K tokens
  (the API long-context billing threshold) -- size read slices well under that.
- Speed/priority is a user preference. If the user has enabled Codex fast /
  priority processing (`/fast`, or `service_tier = "fast"` / `"flex"`), it
  applies; do not force a tier on the user.

### Example: Codex optional custom agents

Codex supports standalone custom agent TOML files under `~/.codex/agents/` for
personal agents or `.codex/agents/` for project agents. Each file needs `name`,
`description`, and `developer_instructions`. Optional fields such as `model`,
`model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, and `skills.config`
inherit from the parent when omitted.

#### `.codex/agents/parallel-explorer.toml`

```toml
name = "parallel_explorer"
description = "Fast read-heavy explorer for bounded codebase, data, and log slices."
model = "gpt-5.6-terra"
model_reasoning_effort = "low"
sandbox_mode = "read-only"
nickname_candidates = ["Atlas", "Kepler", "Noether", "Turing", "Hopper", "Lovelace"]

developer_instructions = """
Stay in exploration mode. Own only the assigned slice.
Prefer rg, targeted file reads, schema inspection, and concise evidence.
Do not edit files.
Return the requested structured handoff with coverage, confidence, and concrete sources.
"""
```

#### `.codex/agents/docs-researcher.toml`

```toml
name = "docs_researcher"
description = "Documentation researcher that verifies APIs, versions, and current behavior through available docs/MCP/web tools."
model = "gpt-5.6-terra"
model_reasoning_effort = "medium"
sandbox_mode = "read-only"

developer_instructions = """
Verify current API and framework behavior from primary documentation when possible.
Include source URLs and call out uncertainty or date-sensitive details.
Do not edit files unless explicitly assigned.
Return the requested structured handoff with confidence labels.
"""

[mcp_servers.openaiDeveloperDocs]
url = "https://developers.openai.com/mcp"
```

#### `.codex/agents/parallel-worker.toml`

```toml
name = "parallel_worker"
description = "Implementation worker for one explicitly owned file or module slice."
model = "gpt-5.6"
model_reasoning_effort = "high"

developer_instructions = """
Own only the assigned files/modules.
You are not alone in the codebase: other workers may be active.
Do not revert changes you did not make. Keep unrelated files untouched.
Run focused verification for your slice and return the code/edit handoff.
"""
```

#### `.codex/agents/reviewer.toml`

```toml
name = "reviewer"
description = "Read-only reviewer for correctness, security, regressions, and missing tests."
model = "gpt-5.6"
model_reasoning_effort = "high"
sandbox_mode = "read-only"

developer_instructions = """
Review like an owner.
Prioritize correctness, security, behavioral regressions, and missing tests.
Lead with concrete findings and evidence.
Avoid style-only comments unless they hide a real bug.
Return the requested structured handoff.
"""
```

#### `.codex/agents/verifier.toml`

```toml
name = "verifier"
description = "Read-only verifier for checking claims against cited sources, commands, counts, or current docs."
model = "gpt-5.6"
model_reasoning_effort = "high"
sandbox_mode = "read-only"
nickname_candidates = ["Verifier", "Crosscheck", "Evidence"]

developer_instructions = """
Your job is verification, not generation.
Check only the assigned claims against the provided sources, commands, or docs.
Do not inspect the generator's reasoning unless explicitly asked.
Return supported, partly-supported, unsupported, or source-not-found per claim.
Quote or cite the exact evidence that settles each verdict.
If evidence is missing or ambiguous, say so and mark confidence low.
Do not edit files.
"""
```

### Example: Codex registering custom agents from config

Standalone files in `.codex/agents/` are the simplest convention. If you want a
config file to declare roles explicitly, Codex's sample config also supports:

```toml
[agents]
max_threads = 6
max_depth = 1

[agents.parallel_explorer]
description = "Fast read-heavy explorer for bounded slices."
config_file = "./agents/parallel-explorer.toml"
nickname_candidates = ["Atlas", "Kepler", "Noether"]

[agents.reviewer]
description = "Find correctness, security, and test risks."
config_file = "./agents/reviewer.toml"
nickname_candidates = ["Ada", "Grace"]

[agents.verifier]
description = "Verify claims against cited evidence without seeing generator reasoning."
config_file = "./agents/verifier.toml"
nickname_candidates = ["Verifier", "Crosscheck"]
```

Paths in `config_file` are relative to the `config.toml` that defines them.

### Example: Codex verification helpers

Codex-native helpers (not required by the skill):

- `spawn_agents_on_csv` for row-shaped verification when available.
- `codex exec --output-schema` for scripted claim-check outputs.
- `approvals_reviewer = "auto_review"` only for approval/security review; do not
  treat it as a general verifier.
- `web_search = "live"` or MCP docs tools when current sources are required.

### Example: Codex `codex exec` fleet pattern

For scriptable parallel writes, create one git worktree per attempt/slice and
run one `codex exec` per worktree:

```bash
git worktree add ../repo-auth-audit -b audit/auth
git worktree add ../repo-api-audit -b audit/api

codex exec --cd ../repo-auth-audit --sandbox workspace-write \
  --model gpt-5.6 -c 'model_reasoning_effort="high"' \
  "Audit and fix auth slice only. Return a code/edit handoff."

codex exec --cd ../repo-api-audit --sandbox workspace-write \
  --model gpt-5.6 -c 'model_reasoning_effort="high"' \
  "Audit and fix API slice only. Return a code/edit handoff."
```

Use `--json` for event streams and `--output-schema` when a script needs
machine-readable results.

### Example: Codex skill location guidance

Current official Codex skill authoring locations:

- Repo-local: `.agents/skills/<skill-name>/`
- User-global: `$HOME/.agents/skills/<skill-name>/`
- Admin/system: `/etc/codex/skills/`
- Bundled system skills: shipped with Codex

Ray's local setup has previously used a `~/.codex/skills` to `$HOME/.agents`
symlink/plugin path, so `~/.codex/skills/<skill-name>/` may work on this
machine. For a portable Codex-native skill, prefer `$HOME/.agents/skills` or
repo `.agents/skills`. The collection itself is still linked by
`bin/agent-skills link`; do not treat `~/.codex/skills` as the skill
requirement.
