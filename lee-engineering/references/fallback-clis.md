# Vendor CLI fallbacks

Read this only when `bin/agent-routes scan` shows a family or capability the current harness cannot
provide. A vendor CLI is a fallback route, never the default way to reach a second model.

Nothing here installs skills. Skill distribution is `bin/agent-skills link`, and there is exactly one
copy on disk.

## Before launching any CLI

1. Check `preferOver` on the route. If it is set, the harness already reaches that family. Stop.
2. Check for a double draw. If the CLI authenticates to a provider account the harness also uses,
   both draw on one meter. Count that pool once.
3. Derive family from the resolved model ID, not the CLI name. A Cursor process running a Grok model
   is a Grok-family route.
4. Only a locally launched process acting on the controlled checkout is eligible. Hosted or
   background workspace delegation, provider-managed VMs, and remote PR agents are not.
5. Tool-confirmation settings change confirmation behavior only. They never widen the writer lease,
   filesystem scope, data route, GitHub authority, network authority, or side-effect authority.
   Enforce those with a bounded checkout, tool denials, and the packet.

## What the scan can and cannot tell you

`bin/agent-routes` reads a model list from any CLI that exposes one: `grok models` and
`cursor-agent models` both list the authenticated account's models, and `grok inspect --json` reports
discovered configuration rather than models, so it is not wired into discovery. None of the vendor
CLIs expose a machine-readable account meter, so their pools come back `unknown`. Treat an unknown pool as one
small packet, then re-scan. Do not infer remaining quota from a successful call.

A CLI that is installed but publishes no model list is recorded in `sources` with that reason. That
is a reportable fact, not a gap to fill by guessing model names.

## Grok CLI wrappers

When a Grok CLI route is the admitted fallback, launch it through the installed wrappers in
`lee-engineering/scripts/`, never the bare `grok` binary:

- `lee-grok` — direct worker. Injects `--always-approve` and rejects `--permission-mode` and a
  caller-supplied `--always-approve`.
- `lee-grok-review` — fixed-artifact read-only review. Pins low reasoning, keeps approve mode,
  disables memory, planning, subagents, web access, and built-in tools, limits the run to one turn,
  and emits streaming Messages JSON. Every component is first-party documented: `--effort low`
  (alias `--reasoning-effort`), `--no-memory`, `--no-plan`, `--no-subagents`,
  `--disable-web-search`, `--disallowed-tools`, `--max-turns 1`,
  `--output-format streaming-messages-json`, and optionally `--sandbox read-only`.
  https://docs.x.ai/build/cli/reference
- `lee-cursor-grok` — Cursor-backed Grok worker. Pins the model and injects `--force`, rejecting
  caller-supplied model, mode, force, yolo, and auto-review flags.

The user-level Grok configuration must also contain exactly the following. It is user-scoped: a
project `.grok/config.toml` cannot set it, and the legacy `approval_mode` and `yolo` keys are still
accepted but lose to `permission_mode`.

```toml
[ui]
permission_mode = "always-approve"
```

Do not use `--permission-mode acceptEdits` for an unattended run. The mode exists and is documented,
but xAI positions it for interactive local coding and steers scripts, SDKs and CI to always-approve;
its own headless example uses `--permission-mode dontAsk` with explicit `--allow` rules. A prior
observation of `stopReason: cancelled` before the first edit tool call under `acceptEdits` on Grok
CLI 1.0.5 is corroborated only by community reports, not by vendor documentation, so treat it as
unverified rather than as a known defect.
https://docs.x.ai/build/features/permissions

For a large review artifact, split it into named immutable slices and put the whole-artifact
fingerprint in every packet. Do not wrap a short watchdog around non-streaming `json`: Grok can
stream reasoning for minutes on a large patch before producing a final result, which is active
inference rather than a hang.

A Cursor-backed Grok route is a separate admission from direct Grok and must pass a fixed one-edit
tool probe before authoring. A direct Grok pass does not prove the Cursor tool bridge.

## When the harness already reaches the model

None of the above applies. Dispatch it as an ordinary in-harness worker: no wrapper, no
permission-mode invariant, no second data route. The capacity pool is the harness's own provider
account.
