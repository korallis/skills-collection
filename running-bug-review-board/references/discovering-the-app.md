# Discovering the app — investigate intent before testing

Bad QA happens when the agent invents tests from the code instead of from
**what the customer is hired to do with the app**. Before writing a
single scenario, spend 10–20 minutes discovering intent.

## Contents

- What to read (in priority order)
- What to extract (mental notes)
- Asking the user (when docs are thin)
- Build a mental model of routes / surfaces
- Identify high-pain-point bugs before testing
- Architecture / pattern files to read
- Output of the discovery step

## What to read (in priority order)

| Source | Yields |
|--------|--------|
| **Product spec / vision doc** (often `docs/PRODUCT_SPEC.md`, `docs/VISION.md`, or pitch deck) | The user-promise — what the customer is hired to do |
| **README / homepage / landing copy** | The marketing voice — how the app describes itself to users |
| **Phase / sprint / milestone doc** | What was just built and why; "Known issues / deferrals" drive scope |
| **Architecture / handoff / agent rules doc** (e.g. `docs/AGENT_HANDOFF.md`, `AGENTS.md`) | Non-negotiable patterns; deviations from these are usually bugs |
| **Existing test plan** (if any) | What's been tested before — extends rather than duplicates |
| **Open bug reports + status** | Re-test fixed/in-progress; honor known P2 deferrals |
| **Latest coordinator merge / sign-off doc** | What's already verified; don't blindly retest |
| **Public route map** (e.g. `app/`, `pages/`, `routes/`) | The surfaces a real user actually touches |
| **CHANGELOG / recent commit messages** | What changed in this build |

If the project follows a different convention (e.g. Linear epics, Jira
tickets, Notion docs), use those. The skill is the workflow; the source of
truth is whatever the team actually uses.

## What to extract (mental notes)

After reading, you should be able to answer:

- **Who is the target user?** (age, role, technical skill — affects what
  "easy" means)
- **What is the primary job-to-be-done?** (one sentence)
- **What are the success metrics?** (e.g. "create group + invite in 2
  minutes", "page loads under 2 seconds")
- **Which device modes, and which is primary?** We test **mobile, tablet,
  and desktop**; the spec's primary target leads. If it's unclear, ask the
  user; if the user isn't available, infer the primary from the repo and
  note the assumption. Record the result in `qa-config.json#platforms.web`
  (`deviceModes`, `primary`, `primarySource`) so later passes don't re-ask.
- **What auth provider, payment provider, data backend?** (affects test
  account playbook and DB verification path)
- **What are the role permissions?** (admin / member / co-admin / etc.)
- **What is in scope for THIS phase vs deferred?** (so you don't fail a
  scenario the team intentionally postponed)

If you can't answer one of these, **ask the user** before writing tests.

## Asking the user (when docs are thin)

If the repo lacks a product spec, phase doc, or test account playbook —
this is common in early-stage projects — ask **before** guessing. A
30-second question now saves hours of irrelevant tests.

### Question templates

**Product intent (when no PRODUCT_SPEC):**

> I'm preparing a real-user QA pass. Before I write the test plan, can you
> confirm in 1–2 sentences: who is the target user, and what is the one
> thing they should be able to do successfully end-to-end after this
> phase?

**Test account playbook (when none documented):**

> I need test accounts for the QA pass. Could you point me at:
>
> 1. Auth provider docs / dev mode for test users (Clerk has +clerk_test
>    + OTP `424242`; Supabase has `seed.sql`; Auth0 has fixture users; etc.)
> 2. An admin account I can use, OR permission to create one
> 3. The convention for test email suffixes per run (e.g. `+run0526`)
>
> If none exists, I can document one as part of the pass.

**Primary device mode (when ambiguous):**

> I'll test mobile, tablet, and desktop. Which is the **primary** target I
> should lead with and weight most heavily — or is there a specific device
> profile (iPhone 14, iPad, 1440px desktop) you care about? If you're not
> around, I'll infer the primary from the repo's responsive setup and note
> the assumption.

**Phase scope (when phase doc is partial):**

> Phase ${N} doc lists `[X, Y, Z]` as built and `[A, B]` under "Known
> issues / deferrals." Do you want me to file P2s on A/B during this
> pass, or leave them entirely out of scope?

**Existing UAT / users (for late-stage phases):**

> Has anyone outside engineering tested this build yet? If so, what did
> they hit? I'll re-run those scenarios first as regressions.

## Build a mental model of routes / surfaces

Sketch the app as a real user encounters it:

```
Public:
  /                  → landing
  /sign-in
  /sign-up           → ?invite=CODE accepted? targetEmail param?

Authenticated (onboarded):
  /dashboard         → today's view
  /[entity]          → list / detail
  /[entity]/[id]     → resource detail
  /settings

Authenticated (not yet onboarded):
  /profile/setup     → can users skip back to public?

Admin-only:
  /[entity]/[id]/settings
  /admin
```

Each surface gets at least one scenario. Negative tests live next to
positive tests on the same surface.

## Identify high-pain-point bugs before testing

Real users hit these failure modes most often. Add a scenario for each
applicable to your app:

| Pain point | Symptom |
|------------|---------|
| **Stale local/session storage across flows** | Returning visitor's old context bleeds into a new flow (BUG-001-style "stale invite in storage"). |
| **Auth ↔ routing race** | User signs in but hits a blank page or wrong destination during the milliseconds when auth state syncs. |
| **Redirect after onboarding** | New user lands somewhere unexpected (no group / no inbox / wrong tenant). |
| **Mobile keyboard hides the submit button** | Form fields scroll under the soft keyboard; user can't see "Save". |
| **Tap target < 44 px** | Old fingers / gloves / stylus miss small buttons. |
| **Modal close affordance hidden behind keyboard or off-screen** | User trapped in modal. |
| **Invite / share link expired or single-use silently** | "Why doesn't my code work?" |
| **Empty state vs zero-state vs error state mixed** | "Group not found" actually means access-denied. |
| **Optimistic UI lies** | Toast says saved; refresh shows it didn't. |
| **Double-submit creates duplicates** | Slow network + impatient user → two records. |
| **Console warnings during routine nav** | Hydration mismatch, dev warnings, missing keys. |

## Architecture / pattern files to read

If the repo has a handoff doc (e.g. `docs/AGENT_HANDOFF.md`,
`AGENTS.md`, `CONTRIBUTING.md`), it usually documents **non-negotiable
patterns** — patterns that, if violated, are bugs by definition. Examples
seen in the wild:

- "Use `useConvexAuth()` not `useAuth()` for Convex query gating" — if a
  page uses the wrong one, you'll see a flicker / redirect race.
- "Invite resolution from URL only, never sessionStorage at submit time"
  — if storage is read at submit, stale-state bugs surface.
- "All redirects via `router.replace`, never hardcoded paths" — if a
  hardcoded path exists, route-changes break it.

When you find a violation in the live app, it's a bug — not a code
review note.

## Output of the discovery step

Before you start scenarios, you should have:

1. A 2-paragraph mental model of the app: target user, job-to-be-done,
   success metrics.
2. The **project type(s)** (web / native macOS / iOS / Electron-Tauri /
   mixed / other) and which playbook(s) activate. A **mixed** monorepo
   (e.g. web + iOS) activates **every** matched playbook — collect all
   surfaces present and never let a web match short-circuit a co-located
   iOS or macOS pass. Plus whether **Codex Computer Use** is available
   (macOS only) for a human-fidelity pass on web apps or to reach a
   native Mac app. Don't assume it's there; most VMs (Cursor cloud, CI)
   lack it, so the pass must still succeed with a browser driver alone.
3. A list of public + authenticated routes.
4. A list of personas with expected permissions per route.
5. A list of recently-changed surfaces (from CHANGELOG / git log) — these
   are highest-risk for regressions.
6. A list of out-of-scope items (defer, do not file as blockers).
7. A list of open bugs to re-test first.
8. The **issue tracker** (confirmed by the user) recorded in
   `docs/qa/qa-config.json` with `discoveredAt` + `confirmedBy`.
9. If there's an existing bug-reports folder: a quick heuristic scan per
   [triage-heuristics.md](triage-heuristics.md) to flag obvious clusters
   so the new pass can avoid filing duplicates.

If anything in (1)–(9) is unclear, **ask the user** before continuing.
