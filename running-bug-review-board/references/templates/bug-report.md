# BUG-NNN: Short title

| Field | Value |
|-------|--------|
| **Status** | open |
| **Priority** | P0 / P1 / P2 |
| **Phase** | {N} |
| **Test ID** | e.g. P{N}-C1 (from manual test plan) |
| **Gate item** | e.g. {N}.4 (from QA_GATES.md) |
| **Reported by** | Name |
| **Reported on** | YYYY-MM-DD |
| **Environment** | local / staging / production |
| **Fixed in** | *(PR link or commit — fill when fixed)* |
| **Verified by** | *(QA name — fill when verified)* |

---

## Contents

- Summary
- Impact
- Risk to fix
- Steps to reproduce
- Expected result
- Actual result
- Environment details
- Evidence
- Notes
- Triage log

## Summary

One sentence describing the bug. Also acts as the "deck" in the HTML
report — set in serif, sits below the title.

---

## Impact

What does a user experience if this ships unfixed? One or two
sentences. Concrete, user-facing language ("anyone who…", "users
who…"). This is what an engineer scans first when triaging — it
answers "do we care?" before "how do we fix?".

Examples:
- "Anyone who briefly considered an invite from a co-worker can be
  silently joined to that group days later, without their consent
  or knowledge."
- "Users on slow connections see a 'saved' toast but their changes
  are silently dropped; they think the data is safe."
- "Cosmetic — the modal close button is 36×36 on iPhone where the
  HIG minimum is 44×44. Users with gloves or accessibility needs
  may miss it."

Rendered as a serif pull-quote in the HTML report. Hidden if empty.

---

## Risk to fix

*(Usually empty at file time; populated by the engineer during the
BRB. Leave blank if QA can't reasonably assess.)*

Engineer's marginal note: how scary is fixing this? One or two
sentences covering the blast radius, the touched surfaces, and any
known coupling. Helps the BRB decide "fix now or defer".

Examples:
- "Local — the invite-resolution code path is a single function in
  `convex/invites.ts`. Low blast radius; covered by integration
  tests."
- "Cross-cutting — touches the auth provider's session handling,
  the router, and the storage abstraction. Needs a coordinated
  change."
- "Unknown — the responsible code was written before our current
  test coverage. Recommend a spike before scheduling."

Rendered as a soft tinted aside in the HTML report. Hidden if empty.

---

## Steps to reproduce

1.
2.
3.

---

## Expected result

What should happen according to the test plan or product spec.

---

## Actual result

What actually happened.

---

## Environment details

| Item | Value |
|------|--------|
| Device / browser | e.g. iPhone 14 Safari (mobile), iPad (tablet), Chrome 1280px (desktop) |
| Account | e.g. fresh incognito, admin@test |
| URL | Full URL when bug occurred |
| Provider-specific (invite code, tenant, share link) | If relevant |

---

## Evidence

### Console errors

```
Paste browser console errors here (last 30 lines, no PII / tokens)
```

### Server / DB

- Backend dashboard observations (table, field values)
- Terminal log snippets if relevant

### Network

- Method, URL, status, sanitized response body (if 4xx/5xx)

### Screenshots

Attach or link screenshots. Place files in `docs/qa/bug-reports/assets/BUG-NNN/` if committed to repo.

---

## Notes

- Regression? (worked before / never worked)
- Related bugs: BUG-XXX
- Suggested fix area: (optional — file or function name; **never** prescribe the fix)

---

## Triage log

| Date | Who | Action |
|------|-----|--------|
| YYYY-MM-DD | | Filed |
| | | |
