# Bug filing — turning failures into actionable reports

A bug is only useful if engineering can act on it. Use the template,
link the Test ID, file immediately on FAIL.

## Contents

- Severity (BRB taxonomy)
- Filing steps
- Title style
- Steps to reproduce
- Expected vs Actual
- Expected
- Actual
- Evidence
- Notes section
- After filing
- Re-test workflow
- Status transitions
- Anti-patterns
- Bug review board (BRB) cadence

## Severity (BRB taxonomy)

| Level | Definition | Action |
|-------|------------|--------|
| **P0** | Blocks core flow; data loss; auth bypass; security | Phase cannot ship; halt QA pass until triaged |
| **P1** | Feature broken or wrong; workaround exists | Blocks current phase sign-off |
| **P2** | Cosmetic, edge case, accessibility, dev console noise | Defer to polish phase or release hardening |

When in doubt between P1 and P0, choose **P0** if a user could experience
data loss or land in a non-recoverable UI state.

## Filing steps

1. Pick the next BUG number:
   ```bash
   ls docs/qa/bug-reports/BUG-*.md | sort -V | tail -1
   ```
2. Copy template:
   ```bash
   cp docs/qa/bug-reports/_template.md \
      docs/qa/bug-reports/BUG-NNN-short-kebab-title.md
   ```
3. Fill in **every** section. Empty sections undermine triage.
4. Save screenshots to `docs/qa/bug-reports/assets/BUG-NNN/`.
5. Add a row to the index table in `docs/qa/bug-reports/README.md`:
   ```
   | BUG-NNN | <title> | P0/P1/P2 | open | <phase> |
   ```
6. Reference the bug ID in your run report's **Results table** Notes
   column.

## Title style

`BUG-NNN-<kebab-case-summary>.md` — describe the **observed behavior**,
not the suspected fix.

Good: `BUG-005-recurring-template-skips-leap-day.md`
Bad:  `BUG-005-fix-cron.md`

## Steps to reproduce

Must be executable by a fresh agent with no context. Include:

- Persona (admin / member / fresh user) + persona email
- Starting URL
- Each click / fill verbatim, with input values
- Wait conditions ("after redirect to X", "when 'Loading' disappears")
- Screenshot timing

Example:

```markdown
1. Open incognito tab; navigate to http://localhost:3000/sign-up?invite=ABC123
2. Wait for banner "Join QA Test Crew"
3. Email: bug005+test+run0526@example.com, password: TestPass2026!
4. Click Continue, enter OTP 424242
5. After redirect to /profile/setup?invite=ABC123, fill Full name "QA B5",
   click Save profile & continue
6. Observe redirect destination
```

## Expected vs Actual

Both are mandatory. **Expected** comes verbatim from the test plan's
Expected column or the phase doc. **Actual** comes from your snapshot /
screenshot.

If they look the same in plain text but the bug is real, the difference
is usually invisible state (URL, query string, storage, server row).
Spell it out:

```markdown
## Expected
After Save → /dashboard (no group membership, no invite query string).

## Actual
After Save → /groups/jh79a3...0ds873zhg
URL preserved invite param: /profile/setup?invite=EQre8usbCu before save.
groupMemberships row written with role=member, group=jh79a3...0ds873zhg.
```

## Evidence

Required for every bug:

- **Console errors** — copy verbatim from `browser_console_messages`
  (last 30 lines). Strip auth tokens / PII.
- **Server / DB state** — relevant table row(s) if a side-effect is
  involved
- **Screenshots** — at least the moment of failure; sequence them
  `01-…png`, `02-…png`
- **URL at failure** — full URL with query string

Optional but valuable:

- Network request that returned an error (method, URL, status, sanitized
  body)
- The accessibility / DOM snapshot YAML from the failing step

## Notes section

Capture:

- **Regression?** Worked in last QA run? (Reference prior run report.)
- **Related bugs** — link by ID
- **Suggested fix area** — file or function name from the architecture
  reference. Helps engineering triage but **never** prescribe the fix.

## After filing

- Set bug status to `open`
- Continue running scenarios — do **not** stop the QA pass for non-P0
  bugs
- If P0: pause QA, ping the user / coordinator, then continue with
  scenarios that don't depend on the broken flow

## Re-test workflow

When engineering ships a fix and updates bug status to `fixed`:

1. Pull the linked Test ID from the manual test plan
2. Run that exact scenario on the rebuilt branch (validate first)
3. On PASS: set status to `verified` with date and your handle
4. On FAIL: leave status `open`, add a new dated section under
   **Triage log** noting what's still wrong; do **not** create a new
   bug for the same issue

## Status transitions

```
open → in-progress → fixed → verified
                          ↘ open (regressed)

open → deferred (P2 only, with phase number noted)
open → wontfix (with rationale)
```

## Anti-patterns

| Don't | Why |
|-------|-----|
| File before reproducing twice | Flake → false bug → wastes triage |
| Use the suspected fix as the title | Pre-decides the solution; confuses engineering |
| Skip Console / Server evidence | Can't debug without it |
| Write "I think this is broken" without specific Steps | Untestable bug |
| File 5 separate bugs for one root cause | Choose the highest-impact one and link the rest as "duplicate of" |
| Mark a P0 as P1 to "not stop the pass" | Hides severity; the next reader thinks it's optional |
| Update a `verified` bug retroactively | Append a new run report instead — preserves history |

## Bug review board (BRB) cadence

The auto QA pass files bugs. The **Interactive BRB** triages them with
the user in the loop — pulled from the configured tracker, heuristics
run, status flips applied, HTML refreshed, minutes written. The two
workflows are intentionally separate so triage bias doesn't contaminate
the auto pass.

Full ceremony: [brb-interactive.md](brb-interactive.md).
Pattern-based suggestions: [triage-heuristics.md](triage-heuristics.md).
Bi-directional tracker sync: [issue-trackers.md](issue-trackers.md).
