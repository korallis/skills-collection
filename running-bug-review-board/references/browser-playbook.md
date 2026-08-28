# Browser playbook — cursor-first, fallback ladder

Drive the app like a real user. Whatever tool the agent has, the playbook
is the same: navigate → snapshot → act on **fresh refs** → capture
evidence → release the tab when done.

## Contents

- Scope: web apps only
- Tool ladder (cursor-first)
- Configuration (`qa-config.json#platforms.web`)
- The universal flow
- cursor-ide-browser specifics
- Chrome DevTools for agents specifics
- Drive like a real human (don't trip the tests)
- browser-use specifics
- Playwright specifics
- Snapshot vs screenshot — when to use what
- Responsive spot-checks (mobile / tablet / desktop)
- Capturing console errors as evidence
- Network capture
- Common UI gotchas (universal)
- Tab discipline (parallel mode)
- Capturing evidence efficiently
- When the browser tool itself is broken

## Scope: web apps only

This playbook covers **web app QA in a browser** — Chrome viewport
emulation, real Safari / Firefox, headless Playwright. If the repo under
QA is an iOS / iPadOS application project, use
[ios-simulator-playbook.md](ios-simulator-playbook.md) instead. Web app
QA does **not** boot iOS simulators; the project-type detection in
[discovering-the-app.md](discovering-the-app.md) decides which playbook
activates.

## Tool ladder (cursor-first)

Use whichever is available. The shape of the work is identical.

| # | Tool | When |
|---|------|------|
| 1 | **cursor-ide-browser** MCP | Default inside Cursor / Claude Code with this MCP installed |
| 2 | **Chrome DevTools for agents** (`chrome-devtools-mcp`) | Strong general-purpose choice. Puppeteer-based with built-in auto-wait (fewer race/stale-ref failures), plus DevTools-grade network/console/Lighthouse/performance/accessibility introspection. Best when you're not in Cursor, or want richer inspection — see [specifics](#chrome-devtools-for-agents-specifics). |
| 3 | **browser-use** MCP | Provider-agnostic; works in many agent environments |
| 4 | **Playwright** (CLI or MCP) | Repo already has it; or for headless CI-style runs |
| 5 | **Codex Computer Use** (macOS) | Human-fidelity pass against the *real signed-in* app — see [computer-use-playbook.md](computer-use-playbook.md). Not available in most VMs/Linux; keep it as an add-on, not a dependency. |
| 6 | Manual + screenshot relay | No browser tool — drive yourself, paste console errors and screenshots into chat |

If multiple work, prefer cursor-ide-browser when running in Cursor — its
snapshot YAML and `browser_cdp` give the richest control. Outside Cursor,
Chrome DevTools for agents is usually the best balance of reliable driving
and deep inspection. Whatever you pick, the run must succeed with what the
environment actually has — most VMs (Cursor cloud, CI) won't have Computer
Use, so never make the pass depend on it.

## Configuration (`qa-config.json#platforms.web`)

Record what you discover so a later pass doesn't re-decide it:

```jsonc
"web": {
  "deviceModes": { "mobile": "375x812", "tablet": "768x1024", "desktop": "1280x800" },
  "primary": "mobile",          // mobile | tablet | desktop — the spec's primary target
  "primarySource": "spec"       // spec | user | inferred | default — how it was decided
}
```

- **Test every mode in `deviceModes`**, leading with `primary`. Adjust the
  width×height values to the app's own breakpoints when the spec names them.
- **Set `primary` from the product spec.** If the spec is unclear, ask the
  user (`primarySource: "user"`). If the user isn't available, infer it from
  the repo's responsive setup and record `primarySource: "inferred"` so the
  next pass knows to confirm. A scaffolded stub starts at `"default"`.

## The universal flow

```
list  tabs                       → see what's open
resize to the mode under test    → mobile 375×812 / tablet 768×1024 / desktop 1280×800
lock  the tab (one agent only)
navigate http://localhost:3000/...
snapshot                         → fresh element refs (REQUIRED before each click)
fill / click / press / scroll
wait_for text / time / network idle
capture console + screenshots on failure
unlock                           → only when fully done
```

Always re-snapshot after navigation, click, or form submit — refs go
stale. "Element X has pointer-events: none" or "ref not found" almost
always means a stale snapshot.

## cursor-ide-browser specifics

Reference: tool descriptors live at
`~/.cursor/projects/<workspace>/mcps/cursor-ide-browser/tools/`.

Common calls:

```
browser_tabs           action: list
browser_navigate       url, newTab
browser_lock           viewId, action: lock|unlock
browser_resize         viewId, width, height
browser_snapshot       viewId, take_screenshot_afterwards: true
browser_click          viewId, ref, element (description)
browser_fill           viewId, ref, value
browser_select_option  viewId, ref, value
browser_press_key      viewId, key
browser_scroll         viewId, direction, amount
browser_console_messages viewId
browser_take_screenshot  viewId
browser_cdp            viewId, method, params  ← raw CDP for advanced cases
browser_highlight      viewId, ref            ← debug refs visually
```

**Important:** never call `browser_cdp` with `Input.*` methods (focus
issues in Electron); use the dedicated input tools instead.

### Setting viewport via CDP

Run each scenario at every mode the app supports — mobile, tablet, and
desktop — leading with the spec's primary target:

```
# mobile
browser_cdp Emulation.setDeviceMetricsOverride
  { width: 375, height: 812, deviceScaleFactor: 1, mobile: true }
# tablet
browser_cdp Emulation.setDeviceMetricsOverride
  { width: 768, height: 1024, deviceScaleFactor: 2, mobile: true }
# desktop
browser_cdp Emulation.setDeviceMetricsOverride
  { width: 1280, height: 800, deviceScaleFactor: 1, mobile: false }
```

### Clearing app storage between scenarios

```
browser_cdp Runtime.evaluate
  expression: "sessionStorage.clear(); localStorage.clear()"
  returnByValue: true
```

### Capturing storage as evidence (before clearing)

```
browser_cdp Runtime.evaluate
  expression: "JSON.stringify({ss: {...sessionStorage}, ls: {...localStorage}, cookies: document.cookie})"
  returnByValue: true
```

## Chrome DevTools for agents specifics

`chrome-devtools-mcp` is Google's official MCP server (now stable). It drives
Chrome via Puppeteer and **automatically waits for each action's result**, so
the "clicked too early / stale ref" failures that plague naive drivers mostly
disappear. It pairs driving with DevTools-grade inspection.

Add it to your MCP client (the exact command varies by client):

```bash
# Claude Code
claude mcp add chrome-devtools --scope user npx chrome-devtools-mcp@latest
# Codex
codex mcp add chrome-devtools -- npx chrome-devtools-mcp@latest
# Generic MCP config
{ "command": "npx", "args": ["-y", "chrome-devtools-mcp@latest"] }
```

Map the universal flow to its tools:

```
navigate_page          url
take_snapshot          → accessibility-tree refs to act on (re-take after nav/click)
take_screenshot        → visual evidence
click / fill / fill_form / type_text / hover / press_key / drag
wait_for               text / condition (in addition to built-in auto-wait)
resize_page            375 × 812  ← primary mobile viewport
emulate                CPU + network throttle, geolocation  ← simulate real conditions
list_console_messages  → console errors with source-mapped stack traces
list_network_requests / get_network_request  → 4xx/5xx evidence
lighthouse_audit       → accessibility / SEO / best-practices gate
evaluate_script        → clear storage, read storage, custom checks
performance_start_trace / performance_stop_trace  → LCP/INP/CLS investigation
```

The recipes elsewhere in this playbook translate directly: viewport →
`resize_page`; console capture → `list_console_messages`; network failure →
`list_network_requests` + `get_network_request`; storage clear → `evaluate_script`.

Useful flags: `--headless` (no UI), `--isolated` (throwaway profile),
`--slim` (3 core tools), `--viewport=375x812`. For multiple agents/tabs on one
server, `--experimentalPageIdRouting` + `--isolated`. *(Flag names verified at
release — check the upstream `chrome-devtools-mcp` README for current options.)*

## Drive like a real human (don't trip the tests)

The most common reason an automated run "fails a test the app actually
passes" is that the browser doesn't look like a person to the site. Two
levers fix the bulk of it:

1. **Attach to the user's real, already-signed-in Chrome** instead of a fresh
   automated profile. A WebDriver-launched browser is exactly what bot
   defenses (Cloudflare Turnstile, hCaptcha, "anomaly detected" on auth) are
   built to catch — and it starts logged out, so every scenario re-fights
   auth. Connecting to the real session sidesteps both. With
   `chrome-devtools-mcp`:
   - **`--autoConnect`** (Chrome 144+): enable remote debugging at
     `chrome://inspect/#remote-debugging`, then the server attaches to your
     running Chrome and shares its state between manual and agent testing.
   - **`--browser-url=http://127.0.0.1:9222`**: for sandboxed/VM setups, start
     Chrome yourself with `--remote-debugging-port=9222` and a **dedicated**
     `--user-data-dir`, then point the MCP at it.

   Security caveat (the reason for the dedicated profile): the remote
   debugging port lets *any* local app drive that browser and it carries your
   real session — don't browse sensitive sites while it's open, and treat it
   like handing someone your logged-in window.

2. **Let the driver auto-wait.** Chrome DevTools MCP and Playwright both wait
   for navigation/network/elements before acting. That removes most of the
   `pointer-events: none` / "ref not found" failures in the
   [Common UI gotchas](#common-ui-gotchas-universal) table below — which are
   usually timing, not real bugs.

**Pick the right tool for the job, too.** This skill's pass is "drive a live
page *and* inspect it like a user," which is squarely where Chrome DevTools
MCP shines. For large nightly cross-browser regression suites, Playwright is
still the right call. For a native macOS app or a maximum-human-fidelity pass,
escalate to [Codex Computer Use](computer-use-playbook.md). Chrome DevTools MCP
is Chrome-only, and emulation is not a real device — for iOS *app* projects use
[ios-simulator-playbook.md](ios-simulator-playbook.md).

## browser-use specifics

browser-use exposes a flat action vocabulary: `goto`, `type`, `click`,
`extract_content`, `take_screenshot`, `evaluate`, `clear_cookies`,
`scroll`. Each scenario step maps directly. Page state is described back
to the agent in natural language.

When using browser-use, prefer `extract_content` to grab the full text
of the current page on errors instead of relying on screenshots alone —
helps with bug evidence.

## Playwright specifics

For projects with Playwright already configured, you can drive scenarios
in `tests/manual/<scenario>.spec.ts` and run with:

```bash
npx playwright test tests/manual/<scenario>.spec.ts --headed
```

Use `page.pause()` for interactive debugging, `page.screenshot({ path:
'docs/qa/bug-reports/assets/BUG-NNN/01-step.png' })` for evidence,
`page.context().clearCookies()` for hygiene.

For one-off scenarios without writing a spec, use Playwright in a REPL
or `npx playwright codegen` to record actions then translate to
imperative steps in the run report.

## Snapshot vs screenshot — when to use what

| Need | Use |
|------|-----|
| Element refs to click / fill | snapshot (YAML / accessibility tree) |
| Visual evidence of bug | screenshot (PNG) |
| Console state | console_messages |
| Network failure | network requests / response |
| Storage state | CDP Runtime.evaluate on storage |
| Layout / overflow at small width | screenshot at exact viewport |

## Responsive spot-checks (mobile / tablet / desktop)

Check every page at each mode the app supports — **mobile 375 × 812,
tablet 768 × 1024, desktop 1280 × 800** — because layout bugs hide at
the breakpoint you skip. Eyeball at every width:

- No horizontal scroll on the body
- Content reflows sensibly across breakpoints (no overlap, no cut-off
  text, no stranded elements at tablet / desktop widths)
- Text contrast readable in the default theme

On mobile (and narrow tablet) especially:

- All tap targets ≥ **44 × 44 px**
- Form fields visible above the on-screen keyboard (focus an input near
  the page bottom and confirm)
- Submit button reachable without scroll-to-find
- Modal close affordance on-screen

File a P2 cosmetic bug if any fail. These accumulate across phases and
get triaged in the polish phase.

## Capturing console errors as evidence

After every interaction (or at end of scenario):

```
browser_console_messages viewId
```

Paste verbatim into the bug's Evidence section — last 30 lines is
plenty. Strip any tokens / personal data from auth headers if present.

Real-user-relevant levels: `error`, `warn`. Ignore `info`/`debug` noise
unless it correlates with the failure.

## Network capture

If a scenario's failure looks like a 4xx/5xx, grab the network event:

```
browser_cdp Network.enable
# trigger the action
browser_cdp Network.getResponseBody     # for the relevant request
```

Or use `browser_network_requests` if exposed by your MCP.

Add the request method, URL, status, and (sanitized) response body to
the bug evidence.

## Common UI gotchas (universal)

| Symptom | Cause / Fix |
|---------|-------------|
| `Element X has pointer-events: none` after click | Form is in `Saving…` state — wait 3s, re-snapshot |
| Cloudflare Turnstile / hCaptcha "loading forever" | Refresh tab; stagger between auth attempts; check provider rate limit |
| `Couldn't find your account` after correct password | Account didn't complete OTP; create with fresh `+runMMDD-N` suffix |
| Blank page after redirect | Auth state not yet ready — see [session-hygiene.md](session-hygiene.md) for the auth ↔ routing race |
| Hydration warning on landing | Often P2 — note in console section, do not fail scenario |
| Action does nothing visually but Convex/DB wrote a row | Optimistic UI mismatch — file a P1 |

## Tab discipline (parallel mode)

If you must shard across multiple agents, **one tab per agent**.
Confirmed via 2026-05-19 Mokuhoe run: shared tabs caused half the shards
to stall on stolen OTPs and lost sessions.

If your tooling can't isolate per-agent (e.g. all agents share the IDE
browser), run **sequentially** instead — see
[sequential-wrapup.md](sequential-wrapup.md).

## Capturing evidence efficiently

For each FAIL:

1. Take screenshot at moment of failure (not the next-page error)
2. Save to `docs/qa/bug-reports/assets/BUG-NNN/01-<step>.png`
3. Copy console errors into bug Evidence section
4. Capture URL at failure (full, with query string)
5. (If side-effect) capture relevant DB row from your backend
6. (If 4xx/5xx) capture network request + status

For each PASS, evidence in the run report can be lighter — usually just
"snapshot confirmed expected text" or a one-line description.

## When the browser tool itself is broken

If `browser_snapshot` returns garbage, `browser_navigate` doesn't move
the tab, or the agent loses control of the browser:

1. `browser_unlock` (release any held lock)
2. `browser_tabs list` — see if the tab still exists
3. If yes: `browser_lock` again and retry one operation
4. If no: `browser_navigate` to a fresh tab and retry

If recovery fails twice in a row, **stop and report**. Don't loop. The
parent agent (or user) decides whether to switch tools or restart.
