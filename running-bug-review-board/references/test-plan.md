# Generating a phase manual test plan

The plan is the contract between engineering, QA, and product. Generate
**before** testing. Even a 30-minute draft beats no plan — agents pick
the wrong scenarios when winging it.

## Contents

- Filename + location
- Derive scenarios from four inputs
- Scenario ID scheme
- Required sections
- How to write a single scenario row
- Personas to enumerate up-front
- Map each scenario to one of these intents
- Regression matrix when needed
- Architecture reference table
- After generating the plan
- When in doubt about a scenario

## Filename + location

```
docs/qa/phase-NN-<slug>-manual-test-plan.md
```

Example: `docs/qa/phase-02-sessions-scheduling-manual-test-plan.md`. Keep
slug aligned with the phase doc filename so cross-links stay obvious.

If the repo uses a different convention (e.g. `tests/manual/`, single
running QA doc), adopt that. The skill is the workflow.

## Derive scenarios from four inputs

| Input | Yields |
|-------|--------|
| Phase doc checkboxes | One scenario per user-visible checkbox |
| QA gates checklist | Each gate item must map to ≥ 1 Test ID |
| Product spec (relevant chapter) | User-flow scenarios (read top-down) |
| Architecture / agent handoff § Role permissions | Negative tests (member can't do admin actions) |

Plus regression: any prior phase that this phase touches gets a small
regression block.

## Scenario ID scheme

`P{phase}-{block}{n}` where:

- **phase** — phase number (0, 1, 2, …)
- **block** — letter grouping (A public, B happy-path, C role-restricted,
  D edge/negative, E mobile/UX, …)
- **n** — scenario number within the block

Examples: `P0-A2`, `P1-C1`, `P2-B3`. Map each to a Gate item ID where one
exists (e.g. `2.5`).

## Required sections

Use [templates/test-plan.md](templates/test-plan.md) as the skeleton. At
minimum:

1. **Header** — phase number, date, gate links, device-mode coverage (mobile / tablet / desktop + primary, from `qa-config.json#platforms.web` if set)
2. **Setup before testing** — env, browser, accounts, data tables to watch
3. **Out of scope** — items deferred to later phases (call out by name)
4. **Scenarios** — grouped by block, each scenario one table row with
   `ID | Scenario | Steps | Expected | Gate`
5. **Regression matrix** (for invite/auth/role-touching phases) — full
   E2E rows across personas
6. **Architecture reference** — pointers to relevant API / component
   files so a bug filer can find the suspect code path
7. **Pass criteria** — restate "all P{N}-* pass, gate green, no open
   P0/P1"
8. **Related** — links to bug-reports, gates, phase doc

## How to write a single scenario row

| ID | Scenario | Steps | Expected | Gate |
|----|----------|-------|----------|------|
| P2-B3 | Admin creates recurring template | `/groups/[id]/schedule` → New recurring → Wed 6:30 AM, minCrew 6, 2-week generate | Template saved; 2 weeks of session instances appear | 2.3 |

Rules:

- **Steps** must be runnable verbatim by a fresh agent with **no prior
  context**. Include URLs, UI labels, exact form values.
- **Expected** is what the user (not the dev) sees + the server-side
  side-effect when relevant.
- **Gate** column is empty if no gate item applies — that's fine.
- One scenario, one outcome. If a step has two side effects, split into
  two scenarios.

## Personas to enumerate up-front

```
| Persona     | Email pattern                                    | Notes |
|-------------|-------------------------------------------------|-------|
| Admin       | admin+test+runMMDD@example.com                   | Creates groups, invites, manages roles |
| Co-admin    | coadmin+test+runMMDD@example.com                 | Promoted from member |
| Member      | member-a+test+runMMDD@example.com                | First invite signup |
| Member B    | member-b+test+runMMDD@example.com                | Second multi-use join |
| Solo        | solo+test+runMMDD@example.com                    | Onboarded, no group |
| Steers / VIP | special+test+runMMDD@example.com                | Special role flag |
```

Adjust prefix / suffix for your repo's convention. The `+test+runMMDD`
suffix lets each pass use unique emails without manual list-keeping.

Match personas to phase needs. Phase that creates 6-person teams needs 6+
members; notifications phase needs both push-on and push-off settings.

## Map each scenario to one of these intents

| Intent | Example block letter |
|--------|----------------------|
| Public / unauth | A |
| Happy path (positive) | B |
| Role-restricted / access control | C / F |
| Returning user / edge case | D |
| UI quality / mobile | E |
| Settings / admin config | G |
| Stub / nav smoke | H |

This makes it easy to shard later (parallel coordinator assigns blocks
per agent).

## Regression matrix when needed

For any phase that touches auth / invites / notifications / payments
(roughly: anything cross-cutting), add a matrix:

| Persona | Entry URL | Expected landing | In group? |
|---------|-----------|------------------|-----------|
| New user + invite | `/sign-up?invite=CODE` | `/groups/[id]` | Yes |
| New user no invite | `/sign-up` | `/dashboard` | No |
| Onboarded + invite (signed in) | `/sign-up?invite=CODE` | `/groups/[id]` via dashboard claim | Yes |
| Already member + invite | `/sign-up?invite=CODE` | `/groups/[id]` silent | Yes |
| Bad code on dashboard | `/dashboard?invite=BAD` | Error toast; stay | No |
| Revoked code | `/sign-up?invite=REVOKED` | "Invite not found" banner | No |

Rows above are an example for an invite system; substitute the
cross-cutting concern in your app.

## Architecture reference table

Add a small table mapping scenarios to suspect code paths so bug filers
can include suggested-fix-area:

```
| Area | Path |
|------|------|
| Schema / DB | convex/schema.ts |
| Public functions | convex/<file>.ts |
| Shared logic | convex/lib/<file>.ts |
| Pages | app/(app)/<route>/page.tsx |
| Components | components/<feature>/<file>.tsx |
```

Adapt for your stack (Next.js, Remix, SvelteKit, Rails, Django, etc.).

## After generating the plan

1. Save to `docs/qa/phase-NN-<slug>-manual-test-plan.md`.
2. Add link to `docs/qa/README.md` table.
3. Add link to phase doc § QA gate.
4. Commit with message: `Generate Phase N manual test plan from spec +
   phase doc.`
5. Proceed to mode selection in
   [parallel-coordinator.md](parallel-coordinator.md) or
   [sequential-wrapup.md](sequential-wrapup.md).

## When in doubt about a scenario

- **Ambiguous expected behavior?** Read product spec to find the
  user-promise; if still unclear, ask the user before testing rather than
  guessing.
- **Two valid interpretations?** Write both as scenarios with different
  IDs and let the test result reveal what the code actually does.
- **Phase doc lists a feature you can't see in the app?** That's exactly
  the gap to find — write the scenario as if the feature exists, run it,
  mark FAIL, file a bug.
- **No gate exists yet?** Write the scenario without a gate ID and add a
  TODO row to the gates checklist.
