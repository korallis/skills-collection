---
name: research
description: Investigate a question against high-trust primary sources and capture the findings as a Markdown file in the repo. Use when the user wants a topic researched, docs or API facts gathered, library or vendor behaviour confirmed, or reading legwork delegated to a background agent.
---

Spin up a **background agent** to do the research, so you keep working while it reads.

Its job:

1. Investigate the question against **primary sources** (official docs, source code, specs, first-party APIs), not a secondary write-up of them. Follow every claim back to the source that owns it.
2. Write the findings to a single Markdown file, citing each claim's source.
3. Save it where the repo already keeps such notes; match the existing convention, and if there is none, put it somewhere sensible and say where.

## Read the web through Firecrawl when it is there

Firecrawl tools are not present in every harness, and a background agent may not inherit the tools
you have. Check your own tool list first, then take the best surface available for each fetch:

1. A Firecrawl tool from the table below, when the harness has it.
2. The harness's own search tool, plus `read` on a known URL.
3. Nothing else. Never call a tool you have not confirmed you have.

If the harness ships a `firecrawl` skill, read it and follow its tool table instead of this one. If a
Firecrawl-backed research agent exists, delegate to it rather than fetching pages inline: it keeps
whole pages out of your context.

| Question shape | With Firecrawl | Without |
|---|---|---|
| Which pages exist on this topic | search, scoped with `includeDomains` to the owning vendor | harness search |
| Error message, library behaviour, API semantics, upgrade breakage | `firecrawl_developer`, which indexes issues, merged PRs, and READMEs | search the issue tracker, then `read` the issue |
| Academic literature or paper full text | `firecrawl_research` | search, then `read` the paper |
| Read one known URL | `firecrawl_scrape` | `read` the URL |
| Read many known URLs | `firecrawl_batch` | `read` each URL |
| Enumerate a docs site before reading it | `firecrawl_map`, then `firecrawl_batch` | `read` the sitemap or index |
| One schema filled from several pages | `firecrawl_extract` | `read` each page, extract by hand |
| Facts behind a login, a form, or pagination | `firecrawl_agent` | ask the user; never improvise credentials |
| PDF, Word, Excel, PowerPoint | `firecrawl_parse` | `read` it if the harness converts documents |

When you are on Firecrawl, these save credits and time:

- Search with `scrape: true` in one call rather than searching and then fetching.
- Ask for the smallest format that answers the question: a question format for one fact, highlights
  for the passages that matter, a summary for the gist.
- Map before you crawl, and always cap a crawl with a limit.
- Only bypass the cache when freshness is the point of the question.

## Evidence rules

- A vendor's own documentation, source repository, changelog, or spec is primary. A blog post
  summarising it is not.
- Record the URL and page title for every claim, and the observation date for anything that moves:
  pricing, model IDs, quotas, retention terms, deprecations.
- When sources disagree, cite both and say which one owns the behaviour.
- Mark anything you could not confirm as unverified. Do not fill a gap with a plausible guess.
- Community reports are evidence that a problem exists, never evidence of what an API does. Label
  them as such.
