# Model naming facts

Evidence for the family and tier tables in [`../../bin/agent-routes`](../../bin/agent-routes) and
[`../../bin/agent-roles`](../../bin/agent-roles). Verified against first-party vendor documentation on
**2026-08-28**.

This file is not an inventory. What a session can actually reach comes from `bin/agent-routes scan`.
This only explains how a model ID is read once the scan has found it.

Re-verify when a vendor renames a tier. A wrong word here silently assigns the wrong model to a role.

## Words that mean the same thing everywhere

Small: `mini`, `nano`, `haiku`, `lite`, `small`, `tiny`, `air`, `terra`, `luna`, `scout`.
Large: `opus`, `ultra`, `heavy`, `large`, `max`, `plus`, `fable`, `sol`, `behemoth`.

Notable evidence:

- OpenAI renamed its tier ladder in the 5.6 family and documents the mapping directly. Sol
  "roughly corresponds to the unsuffixed model tier", Terra "to the mini model tier", Luna "to the
  nano model tier". So `gpt-5.6-terra` and `gpt-5.6-luna` are **small**, not large.
  https://developers.openai.com/api/docs/models/gpt-5.6-sol.md,
  https://developers.openai.com/api/docs/models/gpt-5.6-terra.md,
  https://developers.openai.com/api/docs/models/gpt-5.6-luna.md
- Anthropic's `Fable` is a product line above the Opus/Sonnet/Haiku ladder: "Anthropic's most
  capable widely released model", and the models overview says to use it "for the highest available
  capability". https://platform.claude.com/docs/en/models/fable-5/overview
- Meta's Llama 4 ladder is `behemoth` > `maverick` > `scout`.
  https://ai.meta.com/blog/llama-4-multimodal-intelligence/

## Words deliberately given no weight

A single global word list cannot resolve these, so they are recorded and ignored.

| Word | Why it is ambiguous |
| --- | --- |
| `flash` | Google's `gemini-3.7-flash` is its latest and most capable **stable** model, priced above `gemini-2.5-pro`. Within one generation `pro` > `flash` > `flash-lite`; across generations that inverts. |
| `pro` | Large within a generation, but an older `pro` loses to a newer `flash`, so ranking on it inverts Google's own ordering. Also not a Z.ai model token at all: "GLM-5 Pro and Max" are subscription tiers. |
| `spark` | Small for OpenAI (`gpt-5.3-codex-spark`, "fast, less-capable"). A flagship product name for Meta (`muse-spark`). |
| `fast` | Serving priority, not capability. Cursor sells `Grok 4.6 (Fast)` at double the price for "a faster variant with the same intelligence". MiniMax `-highspeed` and Google `veo-3.1-fast` are the same idea. |

With those excluded, version ordering produces the vendor's own answer: `gemini-3.7-flash` beats
`gemini-2.5-pro`, and `gpt-5.6-sol` beats `gpt-5.3-codex-spark`.

## Restricted releases

`mythos`, `daybreak`, `cyber`. Real models, gated behind separate approval and scoped to security
work, so they are excluded from automatic role assignment.

- Claude Mythos 5 is "offered separately, by invitation only, for defensive cybersecurity workflows
  as part of Project Glasswing", sharing Fable 5's specifications.
  https://platform.claude.com/docs/en/models/mythos-5/overview
- `gpt-daybreak-blue-latest` is "an alias for flagship general-purpose models with safeguards
  calibrated for defensive cybersecurity work", resolving to `gpt-5.6-sol`, and needs separate
  provisioning. https://developers.openai.com/api/docs/models

## Family traps

- **`ministral` does not contain `mistral`.** Mistral's small line would fall through to `unknown`
  on a naive substring. Its specialist models share a `-stral` suffix: `codestral`, `voxtral`,
  `leanstral`, `shieldstral`. https://docs.mistral.ai/models
- **Meta ships two lines.** Llama, and the newer Muse (`muse-spark`, `muse-glimmer`, `muse-image`).
  Muse has no tier words; the suffixes are product names.
  https://ai.meta.com/blog/introducing-muse-spark-msl/
- **Composer is Cursor's, not xAI's.** Cursor states Composer is "built on the same open-source
  checkpoint as Composer 2, Moonshot's Kimi K2.5". It is treated as its own family rather than
  folded into Kimi, because Cursor trains and serves it. No `grok-composer` exists in xAI's own
  catalog, though an aggregator may expose an ID by that name, which reads as Grok lineage.
- **Version digits do not rank capability across product lines.** `claude-fable-5` (June 2026)
  outranks `claude-opus-5` (July 2026); both are version 5. Version is only a within-line signal.
- **Context and parameter suffixes are not versions.** `claude-opus-5-1m` is version 5, and
  `llama-3.1-70b` is 3.1. Some aggregator IDs such as `claude-fable-5-1m` and `gpt-5.6-sol-1m` are
  client-side context selectors rather than first-party model IDs.
- **Dateless Anthropic IDs from the 4.6 generation onward are pinned, not evergreen.** Pre-4.6 short
  forms such as `claude-sonnet-4-5` are moving aliases.
  https://platform.claude.com/docs/en/models/overview

## Vendors with no size vocabulary

xAI (rank by version; `grok-build-0.1` is the cheaper coding sibling of `grok-4.6`), Moonshot Kimi
(rank by K number; `-code` is a domain suffix), MiniMax (`-highspeed` is serving speed). For these,
cost and version carry the ranking.
