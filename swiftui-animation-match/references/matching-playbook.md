# Matching Playbook

How to go from a fuzzy interaction wish to either a system affordance or a
specific catalog entry. Work the three steps in order; most requests resolve
at step 2 without any custom animation.

## Contents

- Step 1: Name the moment
- Step 2: Check what the system gives you free
- Step 3: Match into the catalogs
- Worked examples
- Anti-patterns

## Step 1: Name the moment

Users and PMs rarely ask for an animation by name. They say "make saving
feel better" or "the empty screen is boring." Translate into three facts:

1. **What is the user doing?** Waiting, confirming, toggling, browsing,
   reading, unlocking, erring.
2. **What should they feel?** Reassured (it's working), rewarded (it
   worked), oriented (I moved somewhere), delighted (this product has a
   soul), warned (something broke).
3. **How often does it happen?** Per-tap, per-session, once-ever.

The moment taxonomy (mirrors the catalog groupings):

| Moment | Signals in the request | Catalog group |
|---|---|---|
| Indeterminate wait | "loading", "spinner", "feels slow", "blank while fetching" | Wait states |
| Determinate progress | "download", "upload", "percent", "export" | Progress with a real percentage |
| Action confirmation | "submit", "save", "add to cart", "like", "it should feel satisfying" | Action feedback and confirmation |
| Mode change | "toggle", "dark mode", "on/off", "switch accounts" | Toggles and switches with identity |
| Collection browsing | "cards", "carousel", "deck", "swipe through", "wallet" | Cards and gesture-driven browsing |
| Hero / onboarding | "splash", "welcome", "headline", "first run", "make it pop" | Text and hero moments |
| Input chrome | "composer", "attach", "chat bar", "keyboard accessory" | Input chrome |
| Reveal / unlock | "surprise", "scratch", "prize", "easter egg", "mascot" | Reveals and brand delight |
| Destruction / error / treatment | "delete with drama", "glitch", "filter", "premium feel on photos" | Metal shader effects |

## Step 2: Check what the system gives you free

Modern SwiftUI ships motion that used to require custom work. On iOS 26+
the Liquid Glass design language animates system chrome beautifully by
default — custom motion competes with it, so custom belongs in *content*,
not chrome. Before opening a catalog, check this list:

| Need | System answer first |
|---|---|
| Button/tap feedback | `.sensoryFeedback`, default button styles, `.hoverEffect` |
| Icon state change | `.symbolEffect(.bounce/.replace/.wiggle/.rotate)`, `.contentTransition(.symbolEffect)` |
| Number/text change | `.contentTransition(.numericText())` |
| View state change | `withAnimation(.snappy/.smooth/.bouncy)`, implicit springs (springs are the default; don't hand-roll easing) |
| Screen-to-screen | `NavigationTransition.zoom` (iOS 18+), matchedGeometryEffect within a screen |
| Sequenced motion | `.phaseAnimator`, `.keyframeAnimator` (iOS 17+) |
| Simple loading | `ProgressView` — fine for secondary/inline waits |
| List/scroll polish | `scrollTransition`, `visualEffect`, `scrollTargetBehavior(.paging)` |
| Glass/chrome polish | Liquid Glass (`glassEffect`, iOS 26+) — do not imitate it with custom blur stacks |

**Decision rule:** if the moment is high-frequency (per-tap, per-scroll) or
lives in system chrome, the system answer is almost always right. Custom
catalog motion is for *signature moments*: the interactions the product is
known by, low-to-medium frequency, in content the app owns.

## Step 3: Match into the catalogs

If custom motion earned its place:

1. Pick the catalog group from the moment taxonomy above.
2. Scan entries' **Use when** lines and **Keywords** for the closest fit.
   Search by what the user is doing, not by animation names.
3. Read the entry's **Techniques** line: that is the load-bearing trick to
   preserve. Read **Lift notes** for dependencies and difficulty.
4. Read the actual source files at the entry's **Path** before writing any
   code (clone the repo from `sources.md` if not already available).
5. Adapt per the catalog's lift checklist and the skill's adaptation
   posture (modernize Timers, replace demo tokens, honor Reduce Motion).

When two entries compete, decide by:

- **Register:** does the app's voice allow theatrical (PillLoader,
  LightSwitch bloom) or only quiet-crafted (CircleLoader, Cards Swap)?
- **Frequency:** the more often users see it, the shorter and subtler the
  winner must be.
- **Difficulty budget:** entries are rated easy / moderate / involved.
  Prefer easy entries unless the moment is a signature.
- **Deployment target:** shaders and modern animators need iOS 17+;
  glass-aware entries branch on iOS 26.

## Worked examples

**"Saving a note should feel more satisfying."**
Moment: action confirmation, per-save (medium frequency), feel = rewarded.
System check: `.sensoryFeedback(.success)` + a `.symbolEffect(.bounce)` on
the save icon may already be enough — propose that first. If the product
wants a signature save: Submit Button (morph to spinner) fits async saves
with a success tick; Like Heart Burst is too celebratory for a utility save.

**"The onboarding first screen is flat."**
Moment: hero/onboarding, once-ever, feel = delighted. Theatrical is
allowed. Text Bouncing (touch-scrub headline) if the hero is a title users
touch; TextSwirl for a word-cloud brand moment; Ember Reveal (shader) if a
hero image should materialize. Pick one — not several.

**"Deleting a document should feel consequential."**
Moment: destruction, rare, feel = warned/final. System check: no system
affordance conveys destruction drama. Burn Effect shader (iOS 17+) is the
direct match; on lower targets, a fall-away + fade with a `.heavy` impact
haptic approximates it.

**"Users don't notice the app is syncing."**
Moment: indeterminate wait, ambient/continuous. A spinner overstates it;
Infinity Symbol Path Loader reads as calm always-on sync in a status area,
or Vertical Ripple Dots for a soft ambient panel. If it's a toolbar-sized
slot, stay with `ProgressView` or a small `.symbolEffect(.rotate)`.

**"Our wallet screen needs to feel like real cards."**
Moment: collection browsing, high frequency, feel = oriented + tactile.
Cards Swap (pile cycle + fan) for the stacked-wallet home; Bank Card
(flip + snap carousel) when CVV/back reveal matters; Cards Shuffle for a
lighter deck-of-content pattern. All are drag-threshold + spring-settle;
keep the app's spring feel consistent with whichever you choose.

## Anti-patterns

- Recommending an animation because it is impressive, not because the
  moment calls for it. The catalogs are a menu, not a quota.
- Stacking multiple signature motions on one screen.
- Custom-animating system chrome (tab switches, sheet presentation,
  Liquid Glass surfaces) that already animates.
- Porting demo code verbatim: Timer choreography, `UIScreen.main.bounds`,
  demo palettes, and fake progress timers all need adaptation.
- Ignoring Reduce Motion. Every adopted animation needs a reduced variant.
- Judging motion from code. Run it and watch it before declaring it done.
