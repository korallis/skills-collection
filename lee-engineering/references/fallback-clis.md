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

`bin/agent-routes` reads a model list from any CLI that exposes one. None of the vendor CLIs expose a
machine-readable account meter, so their pools come back `unknown`. Treat an unknown pool as one
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
  and emits streaming Messages JSON.
- `lee-cursor-grok` — Cursor-backed Grok worker. Pins the model and injects `--force`, rejecting
  caller-supplied model, mode, force, yolo, and auto-review flags.

The user-level Grok configuration must also contain exactly:

```toml
[ui]
permission_mode = "always-approve"
```

`--permission-mode acceptEdits` is forbidden: Grok CLI 1.0.5 returned `stopReason: cancelled` before
its first edit tool call under that mode, while the same fixed probe completed with
`--always-approve`.

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
