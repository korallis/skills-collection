---
name: blast-radius
description: Change-impact and completion audit for wide, risky, cross-cutting, or merge-critical work. Use before declaring such work complete to inspect callers and contracts beyond the diff, identify safety facts, exercise the real artifact, and report what is cleared versus still risky.
---

# Blast Radius

Audit the change as a system, not as a patch.

## Trace impact

1. Read the full diff and list changed contracts, types, data shapes, public behavior, configuration,
   persistence, and operational assumptions.
2. Search beyond matching names: inspect callers, producers and consumers, registration paths,
   generated artifacts, tests, migrations, docs, telemetry, and failure recovery.
3. Identify the safety facts that must remain true. Map each fact to evidence or an unresolved risk.
4. For a very wide change, use `arena` or parallel read-only local reviewers on separate impact
   areas, then aggregate their findings. Reviewers run on the `review` role from
   `~/.agents/routing.json` when it exists; otherwise the current model.

## Prove the result

Run the closest checks plus the real user or integration path when available. Inspect artifacts that
commands produce. A green unit test does not prove generated output, UI behavior, wire compatibility,
or deployment configuration unless it exercises those things.

Report three sections:

- **Cleared:** safety facts supported by code and observed verification.
- **Risk:** plausible impacts that remain uncertain, with severity and evidence.
- **Before merge:** concrete required actions. Use “none” only when the audit supports it.
