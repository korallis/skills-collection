# Session hygiene — the silent bug factory

The single biggest source of false QA failures is **stale session state
bleeding across scenarios**. The single biggest source of real bugs that
ship is **the same thing from a real user's POV**. So tracking session
hygiene serves both goals.

This is the reference that pays the most dividends. Read it once, apply
it religiously.

## Contents

- The five hygiene rules
- Why this matters — the BUG-001 case study
- Pre-scenario checklist
- Clearing storage by browser tool
- Auth provider rate limits — known patterns
- Session hygiene + parallel mode
- Detecting stale state mid-scenario
- Resetting between phases / blocks
- Persona suffix discipline
- When to declare hygiene a bug, not a process issue

## The five hygiene rules

1. **Fresh user = fresh storage.** Before any "fresh user" or "no
   invite/no context" scenario, clear app-level storage. Cookies alone
   aren't enough — `localStorage` and `sessionStorage` outlive a logout.
2. **One browser tab per agent.** Parallel agents on a shared tab cause
   auth-provider rate-limits, session bleed, and false failures.
3. **Cool-down between auth attempts.** Auth providers throttle. 30
   seconds between sign-ups is a safe default for Clerk dev keys; check
   your provider's docs.
4. **Unique persona per scenario.** If a scenario needs a fresh user,
   generate a new email with a unique suffix (`+runMMDD-N`). Reusing an
   email that previously hit OTP failure leaves Clerk (or your provider)
   in a stuck state.
5. **Reset between role changes.** Switching from member → admin in the
   middle of a pass should mean a full sign-out and a tab reset, not just
   "click sign out". Cookies and SSR auth state can lag.

## Why this matters — the BUG-001 case study

The single highest-value bug found across the Mokuhoe QA history was
**stale `sessionStorage.mokuhoe_invite_code`** poisoning fresh signup
flows. A user who had previously opened an invite link, then later
visited `/sign-up` with no invite query param, was silently joined to the
old group because the app fell back to sessionStorage when the URL had
none.

This:
- Was invisible from inspection (the code path "worked")
- Was reproducible only by following a real-user sequence (open link →
  abandon → return later → fresh signup)
- Hid for weeks because every engineer test started from a clean tab

The fix was a small UI change. Finding it required **acting like a
returning real user** with stale state, not a dev with DevTools open.

## Pre-scenario checklist

Run this before starting each scenario — copy-paste into your scratch
notes, check off as you go:

```
Scenario hygiene:
- [ ] Persona email is unique to this scenario (suffix bumped if reusing)
- [ ] If "fresh user": cleared sessionStorage + localStorage
- [ ] If "fresh user": signed out of any prior auth session
- [ ] Browser tab: only this agent uses it
- [ ] Last auth attempt was > 30s ago (provider rate-limit safety)
- [ ] Browser viewport set to the device mode under test (mobile / tablet / desktop)
- [ ] DevTools console open, ready to capture
```

## Clearing storage by browser tool

### cursor-ide-browser MCP

```
browser_cdp Runtime.evaluate "sessionStorage.clear(); localStorage.clear()"
browser_cdp Network.clearBrowserCookies
browser_cdp Network.clearBrowserCache
```

For app-specific keys only (preserves others):

```
browser_cdp Runtime.evaluate "sessionStorage.removeItem('your_app_invite_code')"
```

### browser-use

Use the page evaluate or wait_for tool to run JS. browser-use also
exposes `clear_cookies` and `clear_session` actions.

### Playwright

```ts
await context.clearCookies()
await context.clearPermissions()
await page.evaluate(() => {
  sessionStorage.clear()
  localStorage.clear()
})
```

### Manual

DevTools → Application → Storage → Clear site data. Or open an incognito
window per fresh-user scenario.

## Auth provider rate limits — known patterns

| Provider | Symptom | Cooldown |
|----------|---------|----------|
| Clerk dev | "Too many requests" on verify-email | 30s between signups |
| Clerk dev | "No sign in attempt was found" | Tab session lost — fresh tab |
| Auth0 dev | "anomaly detected" / 429 | 60s; reset breached attempt counter in dashboard |
| Supabase local | None — local auth is unlimited | n/a |
| Firebase emulator | None — emulator auth is unlimited | n/a |

If you hit a rate limit, **stop the scenario** and note BLOCKED. Do not
retry-spam — the limit grows. Wait, then resume with a fresh persona.

## Session hygiene + parallel mode

The 2026-05-19 Mokuhoe coordinator run learned this the hard way:

- Three of five parallel agents stalled because they shared one
  cursor-ide-browser tab. Cookies bled, OTPs were stolen by the wrong
  agent, and "no sign in attempt" errors cascaded.
- The fix is **not** to relaunch in parallel. Switch to sequential mode
  ([sequential-wrapup.md](sequential-wrapup.md)).
- For future parallel runs, confirm each agent gets a separate browser
  context (one tab per agent, ideally one provider per agent). If your
  tooling can't guarantee separation, run sequentially.

## Detecting stale state mid-scenario

If a scenario's URL or page content makes no sense given the steps you
just ran, suspect storage:

| Symptom | Suspect |
|---------|---------|
| New signup lands at `/groups/X` instead of `/dashboard` | Stale invite in storage |
| Sign-in lands at a different tenant than the user is in | Stale tenant in cookies / storage |
| Returning user sees onboarding flow again | Auth cookie stale; user table empty |
| Form submit silently 401s | Auth token expired; UI didn't refresh |
| Wrong account name in header after sign-in | Cached profile; refresh / hard reload |

When suspected, capture the storage state before clearing — it's evidence
for the bug report:

```
browser_cdp Runtime.evaluate "JSON.stringify({
  ss: Object.fromEntries(Object.entries(sessionStorage)),
  ls: Object.fromEntries(Object.entries(localStorage)),
  cookies: document.cookie
})"
```

## Resetting between phases / blocks

Between QA blocks (A → B → C), do a full reset:

```
1. Sign out via the UI (catches sign-out bugs)
2. Clear sessionStorage + localStorage + cookies
3. Hard reload (Cmd-Shift-R)
4. Confirm `/` shows public landing or `/sign-in`
```

Anything other than (4) means there's still state leaking — investigate
before the next block.

## Persona suffix discipline

```
Scenario     Persona                                              Pass
P0-B3        qa-b3+test+run0526@example.com                       New
P0-B7        qa-b7+test+run0526@example.com                       New
P1-C1 retry  qa-c1+test+run0526-2@example.com                     Retry, bumped
```

Bumping the suffix on retry guarantees you're not tripping over the
provider's stuck-state cache.

## When to declare hygiene a bug, not a process issue

If you discover that even with perfect hygiene, the user-visible behavior
still depends on prior session state in a way the user can't predict,
**that is the bug**. File a P1.

Example wording for the bug summary:

> User who previously opened an invite link, then later signs up at
> `/sign-up` with no invite parameter, is silently joined to the old
> group because the app falls back to sessionStorage when the URL has
> none. A fresh return-visit flow should not inherit prior session
> intent.
