# iOS Skill Map

This is the curated menu. Pick what the task needs; do not load all of it.

## Contents

- Paul Hudson / Hacking with Swift
- Antoine van der Lee / SwiftLee
- Thomas Ricouard / OpenAI plugin references
- Krzysztof Zablocki / Merowing
- AppCreator / Paul Solt

## Paul Hudson / Hacking with Swift

Canonical directory:

- https://github.com/twostraws/swift-agent-skills

Use for a strong Swift foundation and modern, teachable defaults.

- SwiftUI: https://github.com/twostraws/SwiftUI-Agent-Skill
- Swift Concurrency: https://github.com/twostraws/Swift-Concurrency-Agent-Skill
- Swift Testing: https://github.com/twostraws/Swift-Testing-Agent-Skill
- SwiftData: https://github.com/twostraws/SwiftData-Agent-Skill

Good fit:

- SwiftUI correctness and common pitfalls
- async/await, actors, Sendable, Swift 6 migration
- Swift Testing macros and XCTest migration
- SwiftData models, queries, migrations, CloudKit

## Antoine van der Lee / SwiftLee

Use for detailed implementation references, SwiftLee-style best practices, and
build optimization.

- SwiftUI: https://github.com/AvdLee/SwiftUI-Agent-Skill
- Swift Concurrency: https://github.com/AvdLee/Swift-Concurrency-Agent-Skill
- Swift Testing: https://github.com/AvdLee/Swift-Testing-Agent-Skill
- Core Data: https://github.com/AvdLee/Core-Data-Agent-Skill
- Xcode Build Optimization: https://github.com/AvdLee/Xcode-Build-Optimization-Agent-Skill

Good fit:

- performance-sensitive SwiftUI
- data race safety and Sendable
- modern test patterns
- Core Data stack/fetch/background/migration work
- slow builds, build settings, compiler time, project configuration

## Thomas Ricouard / OpenAI plugin references

Article mentions Thomas Ricouard's iOS/macOS Codex plugins and Codex Monitor:

- Codex Monitor: https://github.com/Dimillian/CodexMonitor
- Official plugins repo: https://github.com/openai/plugins
- Build iOS Apps path from article: https://github.com/openai/plugins/tree/main/plugins/build-ios-apps
- Build macOS Apps path from article: https://github.com/openai/plugins/tree/main/plugins/build-macos-apps

Use for:

- iOS app wiring
- SwiftUI UI patterns
- SwiftUI Liquid Glass APIs where the deployment target supports them
- SwiftUI performance audit/refactor
- App Intents, Siri, Shortcuts, widgets
- macOS AppKit interop, signing, entitlements, packaging, notarization

Note: these paths were referenced by the article, but may move or require a
different plugin registry surface. Verify them against the current
`openai/plugins` repo before installing. If a path moved, search the repo rather
than hardcoding stale paths.

## Krzysztof Zablocki / Merowing

Article references a rules-based system and two public rule files:

- Guide: https://merowing.info/posts/stop-getting-average-code-from-your-llm/
- General rules: https://merowing.info/assets/files/general.md
- Rule loader: https://merowing.info/assets/files/rule-loading.md
- Inject: https://github.com/krzysztofzablocki/Inject
- Sourcery: https://github.com/krzysztofzablocki/sourcery
- Swifty Stack: https://swiftystack.com

Use for:

- architecture and coding standards
- rule selection by context
- dependency injection and view model coordination
- advanced Swift discipline
- hot SwiftUI prototyping with Inject, when the project already supports it

Do not copy private/course-only rules. Use only public files unless Ray provides
access and asks to incorporate them.

## AppCreator / Paul Solt

Article source:

- X article: https://x.com/paulsolt/status/2042716870512353294
- AppCreator: https://super-easy-apps.kit.com/app-creator

Use the idea, not an assumed GitHub install:

- buildable folders so agents can add files without regenerating projects
- Makefiles as stable build/test/run entry points
- `xcbeautify` or XcodeBuildMCP for parseable output
- version tracking for project-template updates

If the user wants AppCreator itself, follow the official signup/download flow.
Do not invent a CLI install command.
