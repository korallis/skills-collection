# Adaptation Notes

These notes record how the original Cursor orchestration skill became this
portable `waves` skill. They exist so future edits keep the WAVE methodology
and do not reintroduce Cursor plumbing or any single-harness worker API as a
requirement.

## Origin

Ray Fernando's WAVES skill (Workers, Aggregate, Verify, Extend) was published
as `waves-codex` under Apache-2.0 at
https://github.com/RayFernando1337/rayfernando-skills. That skill was itself
adapted from a Cursor orchestration skill.

This collection renamed it to `waves` and generalised the runtime contract:
the methodology is harness-agnostic; workers are dispatched the way the
*current* harness dispatches workers.

Phillip Chaffee's public `deep-research` Cursor skill
(https://github.com/PhillipChaffee/.cursor) is a credited influence on
run-shape triage and dependency-aware dispatch.

## What Stayed Portable

- Mental model: discover -> stage -> verify coverage -> decompose -> fan out ->
  handoffs -> verify claims -> synthesize -> second waves.
- Manager/worker separation.
- Worker isolation as a prompting discipline: one slice, one handoff, no
  sibling assumptions.
- Parallel reads as the safest default.
- Fixed handoff format.
- Verification layer: pre-fan-out gate, cheap handoff checks, confidence labels,
  verifier workers, deliverable validation, and escalation.
- Decomposition recipes: data chunks, multi-stream research, repo audit, and
  parallel implementation with explicit ownership.
- Continuous motion until every slice is terminal or explicitly out of scope.
- Entropy-first decomposition: reduce uncertainty (dig locally, then attached
  resources, then ask the user only if it pays) before slicing; cascade a
  decomposition wave into an execution wave; order the plan least-to-most.
- Paper-grounded technique detail, carried from the original skill: probe
  selection that halves the surviving interpretations; ask-vs-act thresholds;
  factored self-verification with open check questions; sample-and-vote with
  agreement as a confidence flag; judge blinding (no authorship labels, both
  orderings); disjoint-family judge panels; atomic-fact checks with
  self-contained rewrites; citation URL-health passes. Sources listed in
  `references/verification.md` ("Grounding") and `references/examples.md`.
- Skill evals: this skill ships `evals/evals.json` + fixtures following the
  Anthropic skill-creator format (prompt + expected_output + expectations,
  graded PASS/FAIL with evidence against with-skill vs baseline transcripts).
- Run mechanics, carried from the original skill: the wave manifest (slice /
  role / effort / depends_on / verification tier) doubling as the completion
  gate; the worker failure ladder (steer/resume or re-spawn narrower once ->
  do it in the manager thread -> carry as `not-covered`); the `.waves/<run>/`
  scratch-dir convention with `synthesis-wave-N.md` compression at the
  barrier; handoff digest caps; and the SWE recipes
  (implement-a-reviewed-plan, row-shaped codemod, CI-failure triage) in
  `references/examples.md`. Worker prompt endings live in
  `references/handoff-format.md` (section "Prompt Endings per Worker Type")
  for every harness.
- Run-shape triage (state the shape in one line before spawning; on the fence
  pick the smaller; never present inline work as wave coverage) and
  dependency-aware dispatch (`depends_on` in the manifest; a wave is every
  slice whose dependencies are met, where met means the dependency's handoff
  has been verified, not merely returned; dependents launch with distilled
  findings folded into their prompts).
  Both portable as-is; adapted from reviewing Phillip Chaffee's public
  `deep-research` Cursor skill (https://github.com/PhillipChaffee/.cursor).

The worker packet is also portable: objective, non-goals, slice, permitted
paths, acceptance, a chosen `routeId` from the scan, and the required return
shape in `references/handoff-format.md`. Dispatch that packet the way the
current harness dispatches workers.

## Harness-Agnostic Swaps

Cursor `Task`, and every other vendor spawn API, map to **the current
harness's worker dispatch**. The stable user-facing contract is: spawn one
bounded worker per slice with a fixed packet, wait for the required handoff
shape, then consolidate. Do not treat any vendor tool name as the skill's
requirement.

Roles replace model slugs. Pick a route from `~/.agents/routes.json` written
by `bin/agent-routes scan`, preferring `sourceKind: harness`. A vendor CLI is
a fallback only for a family or capability the harness cannot provide.
`family` decides review independence; `pool` decides scheduling.

| Source idea | Portable requirement |
| --- | --- |
| Cursor `Task` with `subagent_type` (backgrounded where the surface supports it) | Dispatch one worker per slice the way this harness dispatches workers, usually in one manager turn, then wait and synthesize. |
| Parallel background Task fan-out | Spawn N workers, wait for all requested results, return one consolidated response. Respect the harness worker concurrency cap; if unknown, batch 3–8. |
| Cursor `explore` | A read-only explorer role for read-heavy scouting. Do not assume the worker is air-gapped; shape access with the harness sandbox / tool policy. |
| `generalPurpose` | Manager-chosen role: implementation worker, research worker, or another named role whose instructions are inlined into the packet. |
| `shell` | An implementation / worker role that inherits shell access from the session (or a custom shell-heavy worker if the harness has one). |
| `best-of-n-runner` | Isolated worktrees or equivalent workspaces, plus one worker per attempt. There is no required built-in of this name. |
| `TodoWrite` | The current harness's plan / todo surface. Do not require a vendor-specific plan tool. |
| Frontmatter that disables auto-invocation | A wave run spawns more workers than usual, so prefer explicit invocation where the harness honors an opt-in flag. Harmless if the field is inert. |
| `~/.cursor/skills/<name>/` | Install and discover this skill where the *current* harness looks for skills. |
| "End your turn and wait for completion notifications" | Spawn, continue useful manager-side work, and wait only when blocked; do not busy-poll. |
| "Stage remote data because read-only workers are offline" | Staging is an optimization and safety move (clean inputs, repeatability, fewer credential/rate-limit hits), not always a requirement. Workers may have network / MCP access depending on session policy. |
| "Local workers share one filesystem, so parallel writes are dangerous" | Parallel writes need disjoint ownership or isolated worktrees / sandboxes and manager-mediated merging. Isolation is a coordination problem, not a named CLI. |
| Cloud plugin that fans work out to remote agents | Use scripted / CI worker fleets or an always-on issue-tracker pattern only if this harness already has that surface. Not a requirement. |
| Data-chunk fan-out by many background Task calls | If the harness has a batch / CSV spawn, use it when each row maps to one worker; otherwise one worker per row. |
| Dedicated verifier worker | A reviewer / verifier role. Prefer a different `family` from the author when independence matters. |
| Missing `subagent_type`: unregistered Cursor roles silently became `generalPurpose` | If a named role is not registered, inline its instructions into a generic worker spawn. A missing role is not permission to skip it. Unknown-type failures are a harness detail, not a reason to drop the slice. |
| Re-task a failed / partial worker by resuming its id | Use the harness resume / follow-up if it preserves that worker's context; re-spawn narrower only when the context itself is the problem. Same-slice continuation only. |
| "Verify before you trust" | The manager runs pre-fan-out gates, cheap handoff checks, separate verifier waves, and final deliverable validation. |
| Recursive subplanner (workers spawning workers) | Off by default. Manager-driven sequential waves at depth 1 are the expected shape. |
| Entropy-first decomposition | Portable as-is. Track the living plan on the harness plan / todo surface. |
| "Route scouting / read waves to a fast Cursor model via the `model` field" | Route scouting / read-heavy work to a cheaper / faster harness route from `~/.agents/routes.json` (`sourceKind: harness` preferred). Research needs a capable route with web / docs access. Implementation needs a capable coding route. The manager / coordinator uses a high-capability harness route. |

### What varies by harness (not a reason to fork the methodology)

- Explorer / scouting is a **role**, not an air-gapped worker. Sandbox and MCP
  policy shape actual access.
- Write-heavy parallel workflows can still conflict. Worktrees or disjoint
  path ownership are the isolation boundary.
- Batch / CSV spawn may be missing or experimental. Fall back to one worker
  per row.
- Few harnesses ship a general arbitrary-claim verifier hook. This skill's
  verification layer (verifier workers, tests, schema checks) is the
  portable substitute.
- Custom agent files, skill search paths, and concurrency knobs differ.
  Read the current harness; do not copy another product's config layout
  into this skill as a requirement.
- Recursion caps, if any, cap *workers spawning workers*. They do not cap
  manager-driven sequential waves.

## Why the Final Skill Is Opinionated

This port keeps the original orchestration discipline and changes only the
local gotchas:

- The safest default remains read-heavy fan-out.
- Staging remains useful for clean inputs and repeatability, not because every
  worker is offline.
- Verification is a first-class step because unchecked worker errors compound
  across waves.
- Parallel implementation is allowed only with clear ownership or worktrees.
- Recursion (workers spawning workers) is off by default to prevent accidental
  explosion.
- That recursion default caps *depth only*. It does not cap manager-driven
  sequential waves: continuous motion across second and third waves is
  preserved from the original skill and is the expected shape. Do not let a
  recursion cap leak into "spawn fewer waves" — each open follow-up bullet is
  a candidate second-wave task.

## Historical notes and Codex port details (not requirements)

The first public port targeted OpenAI Codex as the destination runtime. The
notes below are **historical research**, not the skill's contract. Do not
promote these tool names, config paths, or model slugs back into the main
skill body.

### Verified Codex sources

Checked on 2026-06-14 with web search, Ref, Exa, current local `codex exec
--help`, and the active tool registry:

- Codex Subagents: `https://developers.openai.com/codex/subagents`
- Codex Subagent Concepts: `https://developers.openai.com/codex/concepts/subagents`
- Codex Skills: `https://developers.openai.com/codex/skills`
- Codex Config Basics: `https://developers.openai.com/codex/config-basic`
- Codex Config Sample: `https://developers.openai.com/codex/config-sample`
- Codex App Worktrees: `https://developers.openai.com/codex/app/worktrees`
- Codex non-interactive mode / `codex exec`: `https://developers.openai.com/codex/noninteractive`
- Codex approvals and Auto-review: `https://developers.openai.com/codex/agent-approvals-security`
- Codex best practices: `https://developers.openai.com/codex/learn/best-practices`
- OpenAI Symphony post: `https://openai.com/index/open-source-codex-orchestration-symphony/`

The active tool registry in that session exposed `spawn_agent`, `wait_agent`,
`send_input`, and `close_agent`, but not `spawn_agents_on_csv`, even though
official docs describe it as experimental.

Re-checked on 2026-07-03 against the Codex Config Reference
(`https://developers.openai.com/codex/config-reference`) and changelog
(`https://developers.openai.com/codex/changelog`):

- `features.multi_agent` then documented five collaboration tools:
  `spawn_agent`, `send_input`, `resume_agent`, `wait_agent`, `close_agent`
  (stable, on by default). `resume_agent` reopens a closed agent so it can
  receive `send_input` / `wait_agent` again.
- Custom agents are standalone TOML files (one per file) under
  `~/.codex/agents/` or `.codex/agents/`; project agents load in **trusted
  projects only**. Spawning an unknown `agent_type` fails with an error — there
  is no silent fallback (the `default` role is used only when `agent_type` is
  omitted). The skill's "spawn `default`/`worker`/`explorer` with the role's
  instructions inlined" fallback was a recommendation, not documented
  behavior.
- `agents.max_threads` still defaulted to `6`, `agents.max_depth` to `1`;
  `spawn_agents_on_csv` was still experimental (and documented a per-call
  `max_runtime_seconds` override of `agents.job_max_runtime_seconds`).

Re-checked on 2026-07-19 against the subagents doc, config reference, Codex
changelog, the Responses API multi-agent guide, and the openai/codex source
tree (a parallel verification wave with per-claim evidence):

- Official docs no longer enumerated the collaboration tool names. The
  multi-agent V2 surface (code + Responses API multi-agent guide) was
  `spawn_agent`, `send_message`, `followup_task`, `wait_agent`,
  `interrupt_agent`, `list_agents` — note `interrupt_agent`, not
  `close_agent`. The V1 set (`spawn_agent`, `send_input`, `resume_agent`,
  `wait_agent`, `close_agent`) survived only on threads resumed from before
  the V2 runtime metadata existed ("Threads created before runtime metadata
  existed keep the legacy V1 tool surface" — codex-rs session code).
- The documented reasoning-effort ladder on the subagents page was `none`,
  `minimal`, `low`, `medium`, `high`, `xhigh`, `max`, `ultra` (higher/lower
  levels "when the selected model supports" them); the config-reference type
  string was stale (`minimal..xhigh`). For the GPT-5.6 API the ladder is
  `none..max`; `ultra` is a product setting that converts to `max` plus
  proactive multi-agent.
- GPT-5.6 family GA 2026-07-09 (`gpt-5.6` aliases `gpt-5.6-sol`; `-terra`,
  `-luna` tiers). Official Codex subagent guidance at the time: start with
  `gpt-5.6`, use `gpt-5.6-terra` for lighter subagent work,
  `gpt-5.3-codex-spark` for near-instant text-only (Pro). Luna was not
  recommended for subagents in official docs and had a measured long-context
  cliff (MRCR 41.3% at 256-512K vs Sol 91.5%). Codex CLI 0.144.4/5 corrected
  GPT-5.6 context to 272K in clients.
- V2 `spawn_agent` exposed per-spawn `model`/`reasoning_effort` overrides only
  behind `multi_agent_v2.expose_spawn_agent_model_overrides`; custom-agent
  TOML routing always worked. V1 `fork_context` / V2 `fork_turns` (fork parent
  history into a child) existed in code but were undocumented — don't build on
  them.
- V2 delegation payloads (`spawn_agent`/`send_message`/`followup_task`
  messages) were encrypted between model calls, so spawn prompts could no
  longer be audited from local rollout history.
- `thread/start.multiAgentMode` (app-server) shipped June 17 and was already
  deprecated ("Use Ultra reasoning effort for proactive multi-agent
  behavior").
- Desktop threads could receive undocumented `codex_app.*` thread-management
  tools (`create_thread`, `list_threads`, `read_thread`,
  `send_message_to_thread`, `fork_thread`, `handoff_thread`,
  `set_thread_title`, `set_thread_pinned`, `set_thread_archived`) —
  Desktop-local + feature-flag gated; remote/mobile/CLI-started threads and
  pre-feature resumed threads miss them (openai/codex #26907, #25990, #25818
  all open at the time). Basis for an earlier "Coordinator Thread Mode" and
  its probe-then-fallback rule.

Native-delegation deep dive, checked 2026-07-19 against codex-rs source at
main (commit-level evidence), official docs, and July field reports:

- Delegation mode was derived from reasoning effort per turn
  (`core/src/session/multi_agents.rs`): `ultra` -> Proactive, anything else ->
  ExplicitRequestOnly. The injected explicit-mode policy text was "Do not spawn
  sub-agents unless the user or applicable AGENTS.md/skill instructions
  explicitly ask" — skill text is a first-class, documented delegation
  trigger; `ultra` was never required for waves. The deprecated
  `multiAgentMode` app-server params were ignored.
- V2 eligibility was model-catalog-driven: `gpt-5.6-sol` and `gpt-5.6-terra`
  are V2; `gpt-5.6-luna` is V1 (so V2 parents cannot spawn Luna children);
  maintainers stated 5.6 roots can only spawn 5.6+ models.
- Native V2 spawns defaulted to a full-history fork (`fork_turns` defaults to
  `all`; filtered — keeps user/system/final-answer messages, drops reasoning
  and tool output). Full-history forks inherit the parent's agent type, model,
  and effort and REJECT overrides; fresh-context spawns (`fork_turns: none`)
  are the routable shape. Children inherit parent model/effort by default —
  the July quota-burn failure mode (#31814: e.g. 888 model invocations /
  103.6M input tokens across 3 tasks when Sol-Ultra bred Sol-Ultra children).
- Custom TOML role routing was broken on 5.6 V2 at GA (roles -> `agent_role:
  null`, model and sandbox pins ignored — #31814, #32587, #32782). 0.145+
  re-exposes per-spawn `model`/`reasoning_effort` with baked guidance to honor
  them "only when explicitly requested by the user, applicable AGENTS.md
  instructions, or skill instructions" (maintainer: "the model is not good
  enough yet to judge"). V2 exposes `agent_type` only when custom agents are
  registered. Consequence at the time: inlined role instructions + explicit
  per-spawn model/effort requests were the primary pattern; TOML was optional
  tuning.
- V2 did not enforce `agents.max_depth`; the binding limit was
  `multi_agent_v2.max_concurrent_threads_per_session` (default 4 including
  the root; `agents.max_threads + 1` when set). V2 has no `close_agent`;
  lifecycle verbs are `followup_task`, `send_message`, `wait_agent`,
  `interrupt_agent`, `list_agents`.
- Codex CLI/app did NOT use the server-side Responses API multi-agent beta
  (no `multi_agent` request field anywhere in codex-rs); all orchestration was
  client-side. The hosted beta is a parallel implementation of the same six
  actions for API developers.
- Encrypted V2 delegation payloads + children hidden from `/agent` meant
  post-hoc transcript audits were gone; the wave manifest is the spawn-plan
  audit, reviewed before dispatch.

### Codex-only details that must not become requirements

These were accurate for that port and are listed so they are not quietly
re-copied into SKILL.md as if every harness worked this way:

- Do not require `~/.codex/agents/`, `.codex/agents/`, `agents.max_threads`,
  `agents.max_depth`, `update_plan`, `codex exec`, or `spawn_agent` /
  `spawn_agents_on_csv`.
- Do not require GPT-5.6, `gpt-5.6-terra`, `gpt-5.6-luna`, Sol / Terra / Luna
  as model tiers, or `gpt-5.3-codex-spark`.
- Effort field names (`reasoning_effort` vs `model_reasoning_effort`) and
  `service_tier` / `/fast` are product-specific speed levers, not general
  model routing. Routing belongs in `~/.agents/routes.json`.
- `$HOME/.agents/skills` vs `~/.codex/skills` was a Codex authoring-path
  footnote. Install this skill where the current harness discovers skills.
