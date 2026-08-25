# Grok harness installation and fleet verification

The GitHub repository containing this file is the canonical Lee skill source. Install the skill
globally once per execution environment; repositories consume that shared installation and must not
carry private copies.

## Install or update one environment

From a clean, current clone of `korallis/skills-collection`, run:

```bash
python3 lee-engineering/scripts/sync_grok_harness.py install --json
```

The command atomically replaces both `~/.agents/skills/lee-engineering` and
`~/.claude/skills/lee-engineering`, installs `~/.local/bin/lee-grok`,
`~/.local/bin/lee-grok-review`, and `~/.local/bin/lee-cursor-grok`, and changes only
`ui.permission_mode` in
`~/.grok/config.toml`. It is safe to run repeatedly. Repeat `--skills-root` for any additional
harness-specific skill root.

Use `lee-grok` for every direct Grok launch. Do not invoke `grok` directly from an engineering
workflow and do not supply a permission-mode flag. Use `lee-grok-review` for tool-free immutable
review slices; it pins Grok 4.6 at low reasoning with approve mode, memory off, streaming Messages
JSON, one turn, and planning, subagents, web access, and built-in tools disabled. Use `lee-cursor-grok`
for a Cursor-backed Grok route; it pins Cursor Grok 4.6 and approve mode.

## Environment procedure

1. **T3 Connect fleet:** from one linked environment, use `sync_grok_t3_connect.mjs`. It discovers
   every environment linked to the same T3 Connect account, opens a short-lived authenticated T3
   terminal in each environment, updates the dedicated canonical checkout, installs the skill, and
   verifies the digest. This is the required path for the linked MacBook and T3 environments.
2. **MatildaOS server:** pull the canonical repository under `/data`, run the installer with
   `--skills-root /data/matilda/tooling/skills`, and verify as the `lee` user. The existing
   `~/.agents/skills` and `~/.claude/skills` links then see the same tree.
3. **T3Code bootstrap:** run the local installer after cloning or updating the canonical repository
   in every persistent execution environment. An ephemeral environment must run it during every
   bootstrap. Use the T3 Connect fleet command to detect linked-environment drift afterward.

Do not copy credentials or the rest of `~/.grok`. Authentication remains environment-local.

## Verify one environment

```bash
python3 ~/.agents/skills/lee-engineering/scripts/sync_grok_harness.py verify --json
```

The command exits nonzero unless the skill digest matches the canonical source used for verification,
both installed skill roots match that source, each of `lee-grok`, `lee-grok-review`, and
`lee-cursor-grok` is executable and byte-identical to its counterpart in the verified canonical skill
tree, and Grok has exactly one `always-approve` UI setting.

## Converge and verify the T3 Connect fleet

The command uses the existing T3 CLI authorization for discovery and the relay link for transport.
The relay currently requires a short-lived signed-in T3 client `t3-relay` session JWT for remote
execution; pass a mode-0600 token file with `--session-token-file` or set
`T3_CONNECT_SESSION_TOKEN` for the process. Never commit or copy that token to a target environment.
Run from a clean canonical checkout on `main` after the desired commit is published. `apply` fetches
`origin/main`, refuses unless local `HEAD` equals `origin/main`, sends that exact commit as the release
pin, and refuses installation unless every remote canonical checkout resolves to the same commit:

```bash
node lee-engineering/scripts/sync_grok_t3_connect.mjs apply \
  --session-token-file /path/to/short-lived-t3-relay.jwt
```

The command exits nonzero if any linked environment is unreachable, either canonical checkout is
dirty, the release commit differs, a checkout cannot fast-forward, installation fails, approve mode
is absent, any wrapper differs, or a skill digest differs. The report includes the pinned release
commit and expected skill digest. Use `list` for read-only discovery and `verify` to run the installed
verifier without updating the checkout.

## Verify a directly reachable fleet

Run the fleet verifier from the canonical checkout. Each remote target must be reachable through
non-interactive SSH and must already contain the installed verifier:

```bash
python3 lee-engineering/scripts/verify_grok_fleet.py local lee@matilda-srv lee@mac-host
```

The SSH verifier remains useful outside T3 Connect. It exits nonzero for unreachable targets,
configuration drift, wrapper drift, or skill digest differences. Its JSON output is suitable for a
CI/bootstrap artifact.
