---
name: arena
description: Local multi-agent design or implementation competition. Use when several materially different solutions are plausible and selection quality matters. Creates isolated candidates, judges them against shared criteria, and lets the lead agent synthesize and verify the strongest result without cloud agents.
---

# Arena

Use competing local candidates only when diversity is worth the additional work.

## Frame the arena

1. Define the artifact being selected and four to six criteria tied to the real task.
2. Give every candidate the same scope, repository evidence, constraints, and verification target.
3. Select distinct approaches, not cosmetic variations.

## Run candidates

- Dispatch candidates as harness-native subagents. For model choice, read `~/.agents/routing.json`
  (written by the `setup-lee-engineering` skill): candidates run on the `implement` role, judges on
  `review`, which setup guarantees is a different model family. No routing file, or a role with no
  assignment, means run on the current model — the arena still works, with less diversity.
- A separately installed model CLI is an optional extra lens, never a requirement. Never claim a
  named model was consulted unless it actually ran.
- Isolate implementation candidates in separate branches or worktrees. One writer owns each.
- Keep candidates bounded; they should return artifacts and evidence, not lengthy process diaries.
- Do not allow candidates to merge, push, deploy, or mutate shared external state unless the user
  separately authorized it.

## Judge and synthesize

When practical, have reviewers score candidates independently before seeing one another's verdicts.
The lead agent must still inspect all candidates, select the strongest base, graft only clearly better
elements, and run the repository's real verification. Report the criteria, winner, useful rejected
ideas, and evidence. If no candidate clears the bar, say so and redesign.
