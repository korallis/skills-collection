# iOS / iPadOS app testing playbook

Use this playbook **only when the repo under QA is an iOS or iPadOS
application project**. For web-app QA — even on mobile-first
apps — use [browser-playbook.md](browser-playbook.md). Mobile Safari
testing is not in scope for this skill.

When the repo is an iOS app, our skill's job is to orchestrate the QA
pass — read the spec, generate the test plan, file bugs, run BRB.
**Driving the simulator** (taps, swipes, screenshots, accessibility-tree
inspection, build+run, log capture) belongs to the iOS community's
excellent purpose-built skills. This playbook tells the agent which one
to reach for and why.

## Contents

- When to activate this playbook
- Pre-flight
- What this skill provides for iOS app QA
- Companion-skill ladder for iOS app QA
- Recommended stacks per scenario
- Configuration
- What our skill contributes during an iOS pass
- Evidence convention
- Graceful degradation
- Anti-patterns
- Credit

## When to activate this playbook

Add to the discovery step (see [discovering-the-app.md](discovering-the-app.md)).
Strong signals that the repo is an iOS / iPadOS app:

| Signal | What it suggests |
|--------|------------------|
| `*.xcodeproj` or `*.xcworkspace` at repo root | Xcode project — **shared with macOS**; pair with an iOS-specific marker below (`.iOS(...)`, `platform :ios`, `UIDeviceFamily`, `ios/`) before treating it as iOS |
| `Package.swift` with `.iOS(...)` platform | SwiftPM iOS package |
| `Podfile` with `platform :ios, …` | CocoaPods iOS app |
| `ios/` directory at root with Xcode files inside | RN / Expo / Flutter iOS shell |
| `Info.plist` with `UIDeviceFamily` | iOS / iPadOS app |
| App Store Connect / TestFlight referenced in README or CONTRIBUTING | Shipping iOS app |
| `xcconfig` files, `Schemes/`, fastlane config (`fastlane/Fastfile`) | iOS / macOS toolchain |

If the repo is **not** an iOS app project, skip this playbook entirely.

## Pre-flight

- macOS (Apple Silicon recommended).
- Xcode 15+ minimum. Xcode 26 for iOS 26 simulators and baguette.
- The user has at least one of the companion skills below installed
  (or is willing to install one).

```bash
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "iOS app testing requires macOS." >&2
  exit 1
fi
command -v xcrun >/dev/null || { echo "Xcode CLI tools missing." >&2; exit 1; }
command -v axe        >/dev/null && HAS_AXE=1
command -v baguette   >/dev/null && HAS_BAGUETTE=1
command -v idb        >/dev/null && HAS_IDB=1
command -v xcodebuildmcp >/dev/null && HAS_XCBM=1
```

## What this skill provides for iOS app QA

The skill brings the **process** to iOS QA:

- **Discovery** — read the product spec, ship targets (iOS 17+? iPadOS?
  Apple Watch companion?), accessibility / Dynamic Type requirements.
- **Test plan generation** — derive scenarios from the spec, organize
  into P-blocks, map to gates. See [test-plan.md](test-plan.md).
- **Bug template + filing** — structured `BUG-NNN-*.md` reports with
  iOS-specific evidence sections (accessibility-tree dump, console
  log, simulator screenshot, crash log if any). See
  [bug-filing.md](bug-filing.md) and
  [templates/bug-report.md](templates/bug-report.md).
- **Interactive BRB** — triage with bi-directional Linear / GitHub
  sync. See [brb-interactive.md](brb-interactive.md).
- **HTML report** — Apple-language dashboard the team can open in
  Safari and share. See
  [html-report-style-guide.md](html-report-style-guide.md).

What the skill does **not** do: build the app, boot simulators, send
taps, parse `xcresult` bundles, audit accessibility, monitor logs.
For those, lean on the companion skills below.

## Companion-skill ladder for iOS app QA

> **Verified at v0.2 release date.** Check each project's README and
> CHANGELOG for current flags before relying on a specific command.

| Project | Maintainer | What it does | Use when |
|---------|-----------|--------------|----------|
| **[AXe](https://github.com/cameroncooke/AXe)** | [Cameron Cooke](https://github.com/cameroncooke) | Single-binary Swift CLI. Tap by `--id` / `--label` via Apple Accessibility APIs. `describe-ui` returns the accessibility tree as text (cheap observation primitive). `batch` runs multi-step interaction flows. `brew install cameroncooke/axe/axe`. `axe init` installs AXe's own agent skill. | **Default recommendation** for accessibility-driven UI automation on the simulator. Pair with simctl for boot / openurl. |
| **[XcodeBuildMCP](https://github.com/getsentry/XcodeBuildMCP)** | Cameron Cooke / Sentry | 82-tool MCP server + CLI covering the full Apple-platform workflow: `build_run_sim`, `test_sim`, `boot_sim`, `screenshot`, `record_sim_video`, `snapshot_ui` (view hierarchy), `start_sim_log_cap`. Ships its own MCP and CLI agent-skill primers. | Your agent runs in an MCP-capable client and you want one server for build + simulator + log + LLDB. Often the right choice for full agentic loops. |
| **[ios-simulator-skill](https://github.com/conorluddy/ios-simulator-skill)** | [Conor Luddy](https://github.com/conorluddy) | 27 Python scripts wrapping `xcrun simctl` + `idb`. Semantic navigation, WCAG audit, visual diff, test recorder, accessibility audit, app sandbox container inspector, hang watcher, localization audit. 96% token reduction vs raw tools. | You want a batteries-included Python toolkit — especially for accessibility audits and visual diffs across regression runs. |
| **[ios-build-verify](https://github.com/vermont42/ios-build-verify)** | [Josh Adams](https://github.com/vermont42) | Named-intent scripts wrapping `xcodebuild` (with `xcbeautify`) + AXe. Verbs like "verify screen loaded", "audit accessibility for screen", "screenshot a named view". Built and validated against Claude Code + Claude Opus 4.7. | You want a closed agentic loop (build → run → verify → report) with named intents instead of raw CLIs. Strong choice for SwiftUI apps. |
| **[ios-idb-skill](https://github.com/haowu77/ios-idb-skill)** | [Hao Wu](https://github.com/haowu77) | E2E via Meta's [idb](https://github.com/facebook/idb). `device_init`, `device_tap`, `device_step` (tap → wait → auto screenshot), log markers. Cross-agent (agentskills.io standard). | AXe isn't available, or you're already running `idb` for native E2E. Works for simulators **and** physical iPhones. |
| **[baguette](https://github.com/tddworks/baguette)** | [tddworks](https://github.com/tddworks) | Headless simulator boot, 60fps streaming (MJPEG / H.264), taps via SimulatorKit private HID (the path iOS 26 still honors). `baguette serve` exposes a multi-device farm dashboard. `brew install tddworks/tap/baguette`. | iOS 26 simulators on Apple Silicon, high-fidelity gestures, or a browser-based device farm for human inspection during the BRB. |
| **[serve-sim-skill](https://github.com/malopezr7/serve-sim-skill)** | [malopezr7](https://github.com/malopezr7) | Wraps Evan Bacon's [serve-sim](https://github.com/EvanBacon/serve-sim). Taps, gestures, rotation, hardware buttons, **camera injection** (synthetic feeds for camera-using flows), CoreAnimation debug overlays. | React Native / Expo iOS apps, or any flow that needs camera input. |
| **[swiftui-autotest-skill](https://github.com/yusufkaran/swiftui-autotest-skill)** | [Yusuf Karan](https://github.com/yusufkaran) | `/ios-test` and `/add-accessibility` slash commands. Uses Claude Code's computer-use to navigate every screen, capture screenshots, analyze crash logs, run perf checks. Adds `.accessibilityIdentifier()` to SwiftUI views automatically. | Pure-SwiftUI apps where a visual crawl IS the QA. Also great for the first pass on a fresh codebase that hasn't been instrumented for automation yet. |
| **[xcode-build-skill](https://github.com/pzep1/xcode-build-skill)** | [pzep1](https://github.com/pzep1) | Teaches the agent `xcodebuild` + `xcrun simctl` + XCUITest directly, no MCP needed. CLI reference + XCUITest guide. | Minimal-dependency setups, agents that prefer raw CLIs over MCP servers. |
| **[App-Store-Connect-CLI](https://github.com/rudrankriyam/App-Store-Connect-CLI)** + **[app-store-connect-cli-skills](https://github.com/rudrankriyam/app-store-connect-cli-skills)** | [Rudrank Riyam](https://github.com/rudrankriyam) | Go CLI + agent skills for TestFlight uploads, build management, submissions, signing, App Store screenshot capture (via AXe). JSON-first, no interactive prompts. | Post-QA: pushing a build to TestFlight after BRB sign-off, or refreshing App Store screenshots from QA-approved states. |
| **[Foundation-Models-Framework-Example](https://github.com/rudrankriyam/Foundation-Models-Framework-Example)** | [Rudrank Riyam](https://github.com/rudrankriyam) | Example apps for iOS 26 / macOS 26 Foundation Models. Not a testing skill itself, but a useful reference if your iOS app uses the on-device models — surfaces test scenarios the spec might miss. | The app under QA uses Foundation Models or other iOS 26 frameworks. |

If you've built something that should live on this list, see
[extending-the-skill.md](extending-the-skill.md).

## Recommended stacks per scenario

| Scenario | Recommended stack |
|----------|-------------------|
| Full SwiftUI app, accessibility-first | **AXe** for input + **XcodeBuildMCP** for build/test/logs |
| Single MCP for everything (Cursor / Claude Code) | **XcodeBuildMCP** |
| Closed agentic loop with named-intent verbs | **ios-build-verify** |
| Token-efficient toolkit (WCAG audit, visual diff, hang watcher) | **ios-simulator-skill** |
| React Native / Expo on iOS | **serve-sim-skill** or **ios-idb-skill** |
| iOS 26 high-fidelity gestures, device farm view | **baguette** |
| Physical iPhone, not just simulator | **ios-idb-skill** |
| First pass on a SwiftUI codebase without accessibility identifiers | **swiftui-autotest-skill** for `/add-accessibility` then standard pass |
| TestFlight upload after BRB sign-off | **App-Store-Connect-CLI** + Rudrank's skills |
| Minimal-dependency, raw CLI | **xcode-build-skill** |

## Configuration

In `docs/qa/qa-config.json`:

```jsonc
"platforms": {
  "ios": {
    "$comment": "Set enabled=true only when the repo under QA IS an iOS / iPadOS app.",
    "enabled": true,

    "$comment_devices": "Simulator names from `xcrun simctl list devices`. Test plan derives device coverage from here.",
    "devices": ["iPhone 17 Pro", "iPad Pro 13-inch"],

    "$comment_preferred": "Companion skill / CLI the agent reaches for first. AXe|baguette|XcodeBuildMCP|ios-build-verify|ios-simulator-skill|idb|serve-sim|swiftui-autotest|xcode-build.",
    "preferred": "AXe",

    "$comment_scheme": "Xcode scheme for build + test. Optional; companions can auto-detect.",
    "scheme": "MyApp",

    "$comment_minOSVersion": "Minimum supported iOS version per Info.plist. Drives device coverage in the test plan.",
    "minOSVersion": "17.0"
  }
}
```

The agent reads `preferred` to decide which companion's commands to use
first. If the preferred companion isn't installed, the agent surfaces
the alternatives from the ladder above.

## What our skill contributes during an iOS pass

1. **Discovery** confirms the repo is iOS (per signals above), reads
   the product spec, identifies the device matrix, the auth provider
   (Sign in with Apple? Firebase?), and any external dependencies.
2. **Test plan** is generated with iOS-specific blocks:
   - `P{N}-A` Public / unauthenticated
   - `P{N}-B` Happy-path onboarding
   - `P{N}-C` Permissions flows (notifications, camera, location,
     contacts) — these are iOS-specific and easy to miss
   - `P{N}-D` Backgrounding / state restoration
   - `P{N}-E` Dynamic Type + accessibility
   - `P{N}-F` Rotation / iPad-specific layouts
   - `P{N}-G` Push notifications / deep links
   - `P{N}-H` In-app purchases / StoreKit (if applicable)
   - `P{N}-I` Crash / hang resilience
3. **Bug filing** uses the standard template plus an iOS-specific
   evidence section: simulator screenshot, accessibility-tree dump
   (via `axe describe-ui` or `snapshot_ui`), console log, crash log if
   any, and the device + iOS version + scheme.
4. **The agent delegates** the actual simulator driving to the
   `preferred` companion skill. It does **not** reinvent boot,
   tap, screenshot, or build orchestration.

## Evidence convention

Save iOS evidence under `docs/qa/bug-reports/assets/BUG-NNN/ios/`:

```
assets/BUG-NNN/ios/
├── 01-screen-name.png             # screenshot
├── accessibility-tree.txt         # `axe describe-ui` or similar dump
├── console.log                    # device log capture
└── crash.crash                    # if applicable
```

The HTML report's bug detail page has a dedicated **iOS Simulator
screenshots** gallery section that lazy-loads tiles from that path.
See [html-report-style-guide.md](html-report-style-guide.md).

## Graceful degradation

| Situation | Behavior |
|-----------|----------|
| Repo isn't an iOS app project | Skip this playbook entirely. Don't suggest installing iOS tools. |
| On Linux / non-Mac cloud agent, repo is iOS | Skill says: "iOS app QA is macOS-only — orchestrate from a Mac with Xcode installed." Continue with code review only. |
| macOS but no Xcode | Tell the user to install `xcode-select --install` and at minimum one companion skill. |
| No companion skill installed | Recommend **AXe** as the default install (`brew install cameroncooke/axe/axe` is the lowest-friction option). Fall back to `xcrun simctl` for build / boot / screenshot until they install. |
| iOS 26 simulator, baguette not installed | Suggest `brew install tddworks/tap/baguette`; in the meantime, AXe still works through iOS 26 with the usual caveat. |

## Anti-patterns

| Don't | Why |
|-------|-----|
| Use this playbook to test a web app on Mobile Safari | Out of scope. Use [browser-playbook.md](browser-playbook.md). |
| Reinvent simctl wrappers / tap helpers in our scripts | The iOS community already built better ones — point at them. |
| Mark a scenario PASS from XCUITest passing alone | XCUITest passing means the build compiles and the test ran; it doesn't mean the user-visible behavior is right. Spot-check with a real screenshot. |
| Skip the accessibility block in the test plan | iOS users rely on Dynamic Type and VoiceOver; if QA doesn't catch it, the App Store reviewers will. |
| Ship a build without re-running the QA pass on the device matrix | Simulators don't catch every physical-device bug, but they catch most layout / permission / Dynamic Type bugs. Match the spec's minOS. |
| File an iOS bug without device + iOS version | Engineering can't reproduce without it; add to the environment details. |

## Credit

This playbook stands on the iOS community's work. Major thanks to:

- **[Cameron Cooke](https://github.com/cameroncooke)** for
  [AXe](https://github.com/cameroncooke/AXe) and
  [XcodeBuildMCP](https://github.com/getsentry/XcodeBuildMCP), and for
  popularizing the accessibility-tree-as-observation-primitive pattern.
- **[Rudrank Riyam](https://github.com/rudrankriyam)** for the
  [App Store Connect CLI](https://github.com/rudrankriyam/App-Store-Connect-CLI)
  and [companion skills](https://github.com/rudrankriyam/app-store-connect-cli-skills),
  threading QA evidence through to TestFlight and review.
- **[Conor Luddy](https://github.com/conorluddy)** for
  [ios-simulator-skill](https://github.com/conorluddy/ios-simulator-skill),
  the inspiration for layered helper-script skills, and the
  [Bringing Accessibility into the AI Coding Workflow](https://www.conor.fyi/writing/ai-access)
  post.
- **[Josh Adams](https://github.com/vermont42)** for
  [ios-build-verify](https://github.com/vermont42/ios-build-verify),
  for naming intents over raw CLIs.
- **[tddworks](https://github.com/tddworks)** for
  [baguette](https://github.com/tddworks/baguette), for the iOS 26
  input path.
- **[Hao Wu](https://github.com/haowu77)**,
  **[malopezr7](https://github.com/malopezr7)**,
  **[Yusuf Karan](https://github.com/yusufkaran)**,
  **[pzep1](https://github.com/pzep1)**, and the many others building
  in the open under [agentskills.io](https://agentskills.io).
