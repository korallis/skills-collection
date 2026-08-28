# Catalog: Shubham0812/SwiftUI-Animations

- **Source:** https://github.com/Shubham0812/SwiftUI-Animations
- **Pinned commit:** `2f5b377abc2f273143befa5ad31c63d1304c7faf` (analyzed 2026-07-15)
- **License:** Apache-2.0 (free to lift into commercial and personal apps)
- **Deployment floor:** iOS 17.0 (the effective target in `project.pbxproj`; the SwiftUI Shader APIs used by every shader entry require iOS 17+)
- **Coverage:** 30 animation folders under `SwiftUI-Animations/Code/Common/Animations/` plus 7 Metal shaders under `SwiftUI-Animations/Code/Common/Shaders/`
- **Previews:** every entry ships a `#Preview` / `PreviewProvider`, so each one runs standalone in Xcode Previews

All paths below are relative to `SwiftUI-Animations/` inside the repo. Read
the actual source before lifting; entries summarize, they do not replace the
code. Read [Shared infrastructure](#shared-infrastructure) before lifting
anything, and run the [Lift checklist](#lift-checklist) after.

---

## Contents

- Wait states (indeterminate loaders)
- Progress with a real percentage
- Action feedback and confirmation
- Toggles and switches with identity
- Cards and gesture-driven browsing
- Text and hero moments
- Input chrome
- Reveals and brand delight
- Metal shader effects (all iOS 17+)
- Shared infrastructure
- Recurring motion vocabulary in this source
- Lift checklist

## Wait states (indeterminate loaders)

### Gradient Arc Circle Loader
- **Path:** `Code/Common/Animations/CircleLoader`
- **Files:** `CircleLoader.swift`
- **What it shows:** Classic circular indeterminate progress: soft gradient track ring with a thicker cyan-to-blue rounded arc that spring-settles, sweeps about two turns, expands along the ring, then collapses and repeats.
- **Use when:** Generic app-wide indeterminate progress, login/network "working" waits. The most product-neutral spinner in this catalog; reach for it first when the brand voice is quiet.
- **Feel and juice:** `animationDuration = 0.75`; spring snap `response: 1.5`; sweep `easeInOut(1.5)`; arc expands `circleEnd` 0.325 to 0.925, then collapses with `easeOut(0.75)`.
- **Techniques:** `trim(from:to:)` + `rotationEffect` phased with Timers; dual `Circle().stroke` layers; `LinearGradient` fills; `lineCap: .round`. Modernize the four phases with `.keyframeAnimator`.
- **Lift notes:** Depends on four gradient colors from `Colors.swift`. Single file, ~112 lines. Difficulty: easy. Parameterize line widths, frame (200), spring response, colors.
- **Keywords:** circular progress, trim arc, gradient spinner, indeterminate, spring settle, ring loader, network wait, classic spinner

### Dual Arc Hand-off Spinner
- **Path:** `Code/Common/Animations/SpinningLoader`
- **Files:** `SpinningView.swift`
- **What it shows:** A large outer arc and smaller inner arc take turns expanding and collapsing while rotating through deliberately over-360-degree keyframes (365 to 990 degrees), creating a continuous sweeping hand-off rather than one spinning ring.
- **Use when:** Compact but premium indeterminate spinner for overlays, sheet content loads, or medium waits where a stock `ProgressView` feels cheap but a full scene loader is too much.
- **Feel and juice:** `animationDuration = 1.35`; phase 1 `easeOut` expand/collapse; mid nudge `easeIn`; phase 3 `easeOut(1.35)` + `linear`; rotation resets snap without animation so the loop never reverse-travels.
- **Techniques:** Over-360-degree rotation keyframes so interpolation never short-paths; dual `Circle().trim` + `rotationEffect`; `RotationDegrees` enum; Timer phase machine. Ideal candidate for `.keyframeAnimator`.
- **Lift notes:** `Color.background` only. ~153 lines. Difficulty: moderate. Parameterize sizes (130/48), line width (18), duration, angle table.
- **Keywords:** dual arc, spinner handoff, over-rotation, trim expand, nested circles, indeterminate, compact loader, keyframe angles

### Square Corner Capsule Chase Loader
- **Path:** `Code/Common/Animations/Loader`
- **Files:** `LoaderView.swift`, `LoaderState.swift`, `Support Shapes/Loader.swift`
- **What it shows:** Three stroked capsules stretch and slide around an invisible square (down, right, up, left), chasing each other with staggered start offsets for perpetual motion.
- **Use when:** Mid-size indeterminate wait with geometric personality: modal overlay, "loading more" in a list, or a distinctive alternative to a circular spinner when the UI language is linear/rounded bars.
- **Feel and juice:** Stretch/contract `easeOut(0.35)`; direction cycle every 2.1s; child stagger delays 0.35 / 1.05 / 1.75s; capsule rest 40x40, stretch +72.
- **Techniques:** Direction enum with stretch-then-contract geometry; alignment anchors; nested Timers. Uses deprecated `.animation(_:)` without `value:` (pre-iOS 15 style) — replace with explicit `withAnimation` + `.phaseAnimator`.
- **Lift notes:** No custom colors or haptics. ~265 lines. Difficulty: moderate. Parameterize capsule dimension, stretch offset, stagger delays, stroke width.
- **Keywords:** capsule chase, square path, stretch contract, staggered loaders, geometric spinner, indeterminate, bar loader

### Vertical Ripple Dot Loader
- **Path:** `Code/Common/Animations/Loader2`
- **Files:** `LoaderIIView.swift`, `Support Shapes/MovingCircleView.swift`
- **What it shows:** Seven dots stacked vertically, each oscillating left/right with alternating start direction and slightly different periods, so the stack forms an organic drifting wave rather than a locked metronome.
- **Use when:** Soft ambient wait: a full-height cousin of the chat "typing" indicator, audio/visualizer-adjacent UX, or when a circular spinner feels too busy. Fits dark UIs.
- **Feel and juice:** Per-dot durations 1.00 to 1.15s (non-uniform on purpose — the phase drift is the juice); offset +-15; `easeInOut`; soft white `shadow(radius: 5)` glow.
- **Techniques:** Composition of independently timed oscillators with no shared master clock; Timer + `withAnimation` half-cycles. Easy to rebuild with `.repeatForever` animations.
- **Lift notes:** `Color.label`. ~186 lines. Difficulty: easy. Parameterize count, spacing, offset, duration table, glow.
- **Keywords:** wave dots, vertical ripple, typing indicator, oscillation, ambient loader, phase drift, soft glow, organic motion

### Infinity Symbol Path Loader
- **Path:** `Code/Common/Animations/InfinityLoader`
- **Files:** `InfinityView.swift`, `Support Shapes/InfinityShape.swift`
- **What it shows:** A gray infinity outline with a bright segment looping endlessly along a four-curve lemniscate; wrap-around is handled by duplicate trim layers so the segment never vanishes at the seam.
- **Use when:** Continuous / always-on sync, streaming, or background-work states; abstract calm brand moments. Strong as a centered hero loader.
- **Feel and juice:** `linear(duration: 2.0).repeatForever(autoreverses: false)` driving a 0-to-1 phase; stroke width 20; segment ~0.1 of the path.
- **Techniques:** Animatable trim phase + wrap-around duplicate strokes on a custom `Shape` (four cubic Beziers). Cleanest modern pattern among the loaders — no Timer choreography.
- **Lift notes:** `Color.background`, `Color.label`. ~113 lines. Difficulty: easy-moderate (the shape math is the lift). Parameterize duration, stroke width, segment length, track opacity.
- **Keywords:** infinity, lemniscate, path trim, continuous loop, sync loader, abstract spinner, wrap-around trim, figure eight

### Triangle Stroke + Bouncing Dot Loader
- **Path:** `Code/Common/Animations/TriangleLoader`
- **Files:** `TriangleLoader.swift`, `Support/TriangleShape.swift`
- **What it shows:** A partial stroke slides around a triangle outline while a small circle springs between vertices; auto-starts on appear and loops.
- **Use when:** Geometric or playful brand waits, game-adjacent loading, or when you want spring juice on a path follower. Not for tiny toolbar slots.
- **Feel and juice:** Step 0.7s; stroke `easeInOut(0.7)`; dot `.spring(response: 1.4, dampingFraction: 0.85)` per hop; a no-animation stroke snap avoids reverse-travel artifacts at loop end.
- **Techniques:** Phase enum mapping trim ranges + vertex offsets; `.trim` on a stroked shape; spring-driven `offset` for the marker; Timer orchestration.
- **Lift notes:** `Color.background`; `circleColor` is already a parameter. ~214 lines. Difficulty: easy-moderate. Circle offsets must scale with triangle size; the shape draws its path twice (redundant — fix when lifting).
- **Keywords:** triangle loader, path trim, spring vertex hop, geometric spinner, phase machine, bouncing indicator, custom shape

### 3D Cube Face Loader
- **Path:** `Code/Common/Animations/3dLoader`
- **Files:** `RotatingLoaderView.swift` + 4 support views
- **What it shows:** A rounded card flips like a cube: a white face (dashed spinning ring + orbiting dots) trades places with a dark face (equalizer bars, then typing-style dots). Faces hinge from the edges via 3D rotation.
- **Use when:** Full-screen or splash-level waits where the product wants a crafted, premium-OS moment — onboarding, long cold-start, a branded pause between major screens. Not inline progress.
- **Feel and juice:** 3.5s dwell then flip with `Animation.smooth(duration: 1)`; dashed ring linear 5s forever; bars stagger 0/0.2/0.4/0.6s; dots stagger 0/0.2/0.4s.
- **Techniques:** Perspective hinge via `rotation3DEffect` + edge `offset`; a rotation-state enum packs (degree, offset, anchor, axis); Timer state machine; `StrokeStyle(dash:)`. Prefer `.phaseAnimator` over nested Timers when modernizing.
- **Lift notes:** `Color.background`, `Color.materialBlack`. ~480 lines across 5 files. Difficulty: involved (multi-view orchestration + hinge math). Parameterize face size, dwell/flip durations, which inner loaders cycle.
- **Keywords:** 3d cube flip, rotation3DEffect, hinge, dash spinner, equalizer bars, splash loader, premium wait, card flip

### Book Open/Close Loader
- **Path:** `Code/Common/Animations/BookLoader`
- **Files:** `BookLoaderView.swift`, `BookPagesView.swift`, `Support Shapes/BookHold.swift`
- **What it shows:** Two capsule covers and a U-shaped spine open flat, fan out 15 capsule pages, then close left/right alternately in a continuous loop.
- **Use when:** Reading, learning, document, or knowledge-product waits (article fetch, PDF open, lesson load); a delightful "preparing content" or empty-state moment.
- **Feel and juice:** Phase duration 0.4s; pages stagger `delay(0.084 * n)` across 13 capsules; open uses `easeOut`, covers rotate on `linear`; light impact haptic on tap-to-start.
- **Techniques:** Enum-driven layout state machine mapping each phase to a 6-tuple of offsets/rotations; custom `Shape` spine with round caps; Timer choreography that polls a `@Binding` until started. Replace polling with `.onChange` / `.phaseAnimator`.
- **Lift notes:** `HapticManager`, `Color.background`. ~355 lines. Difficulty: involved. Parameterize cover width, page count/stagger, duration, auto-start vs tap.
- **Keywords:** book loader, page fan, reading wait, capsule covers, custom shape spine, content preparing, document loading

### GitHub Octocat Path Tracer
- **Path:** `Code/Common/Animations/GithubLoader` (shape lives in `Octocat-Wink/Support Shapes/OctocatLoader.swift`)
- **Files:** `GithubLoader.swift` + external `OctocatShape`
- **What it shows:** A dim mascot outline with a brighter trimmed stroke segment chasing around the silhouette like a comet; pauses at path end then resets.
- **Use when:** Brand-mascot or developer-tooling waits where the silhouette itself is the brand signal. The technique generalizes: swap in any brand's outline path.
- **Feel and juice:** Timer every 0.35s advances `strokeEnd += 0.1` with `easeOut(0.5)`; fixed trim window length 0.3; 1s pause at completion.
- **Techniques:** Traveling trim window on a complex custom `Shape`; dual-layer stroke (ghost + active).
- **Lift notes:** `Color.background`; must bring the ~100+ line Bezier path (or substitute your own brand path). Difficulty: moderate (easy animation, heavy path dependency). Parameterize segment length, step, tick interval, brand path.
- **Keywords:** mascot loader, path tracer, trim chase, brand silhouette, stroke comet, outline animation, logo loader

### Pill Spin-Split Wave Fill Loader
- **Path:** `Code/Common/Animations/PillLoader`
- **Files:** `PillLoader.swift` + 6 support files
- **What it shows:** A tall outlined pill spins ~540 degrees, splits open, magenta liquid rises with dual sine waves, particle dots burst upward, then it resets and loops — on a gradient backdrop with floating accent shapes.
- **Use when:** Playful, high-juice branded waits: consumer apps, health/meds metaphors, "refill/charge" moments, splash screens. Too theatrical for dense tool UIs or small inline progress.
- **Feel and juice:** Spin `interactiveSpring(response: 0.64, dampingFraction: 1)`; fill `easeIn(0.79)`; wave phase ticks every 10ms; three staggered particle bursts.
- **Techniques:** Multi-phase Timer machine + sine-wave `Shape` fill + capsule trim/mask; dual wave layers masked by a half-capsule. Replace the 10ms Timer with `TimelineView`; the folder ships a duplicate `Pill` symbol (`Pill.swift` vs `Pill 2.swift`) — deduplicate when lifting.
- **Lift notes:** `Color.pillColor` + inline gradients. ~450+ lines. Difficulty: involved. Parameterize fill color, rotation count, wave amplitude, particle targets, cycle period.
- **Keywords:** pill loader, liquid fill, wave shape, particle burst, spin split, capsule mask, playful splash, high juice

---

## Progress with a real percentage

### Circular Download (liquid ring)
- **Path:** `Code/Common/Animations/Circular Download`
- **Files:** `CircularDownloadView.swift` + 3 support shapes
- **What it shows:** A circular meter: an arrow springs in, morphs into a falling droplet, then a dual half-ring progress sweep + rising sine-wave "water" fill + monospaced percentage; at 100% a tick draws in.
- **Use when:** A single hero download or export with a playful "filling vessel" metaphor — the primary affordance of a screen, not a dense list row.
- **Feel and juice:** Arrow entrance `.spring(response: 0.55, dampingFraction: 0.825)`; tap anticipation (lifts before dropping); 4s linear ring sweep; tick `easeOut(0.35)`.
- **Techniques:** `animatableData` Shape morph (arrow to droplet) + mirrored `Circle.trim` progress + masked sine-wave fill; three-case download state enum; Timers simulate progress. Wire to real progress callbacks; consider `.keyframeAnimator` for the drop morph.
- **Lift notes:** Shares `DownloadState` with Download Button; `Color(hex:)` helper. ~445 lines. Difficulty: involved. Parameterize duration, fill color, progress source, ring size.
- **Keywords:** download progress, circular progress, liquid fill, arrow morph, droplet, percentage, completion tick, ring meter

### Download Button (slot-machine states)
- **Path:** `Code/Common/Animations/DownloadButton`
- **Files:** `DownloadButton.swift` + 5 support files
- **What it shows:** A 320x76 pill cycles Download (dark) / Downloading (teal + capsule progress bar) / Finished (blue) via vertical panel slides behind a mask; the left icon goes static arrow, looping masked arrow, then circle-plus-tick stroke draw.
- **Use when:** Inline CTA for a downloadable asset (app update, PDF, media) where state labels must be unmistakable and the button should auto-return to idle after success.
- **Feel and juice:** Medium impact haptic on tap; panel slides `easeOut(0.35)`; success holds 2.5s then resets; looping arrow sweeps 0.5s with instant snap-back outside the mask.
- **Techniques:** Masked vertical-offset "slot machine" of three state panels + `@Observable` model; progress via `Capsule.trim(to: progress/2)` rotated 180 degrees; overlay icon switches per state. Drive from real `URLSession` progress; two near-duplicate `DownloadStateView` files exist — consolidate when lifting.
- **Lift notes:** `HapticManager`, several palette colors. ~650 lines. Difficulty: moderate-involved. Parameterize dimensions, colors, auto-reset delay.
- **Keywords:** download button, progress CTA, state machine, slot machine, label slide, trim capsule, auto reset, three-state button

---

## Action feedback and confirmation

### Like Heart Burst
- **Path:** `Code/Common/Animations/Like`
- **Files:** `LikeView.swift`
- **What it shows:** A large heart fills with a red gradient, spring-pops to 1.3x, shoots 14 colored capsules radially, expands a fading ring, blooms a radial glow, and floats a swaying "+1" capsule upward.
- **Use when:** Favorite / like / love actions that deserve celebration (social, wishlist, reactions). The best modern-API exemplar in the catalog: no Timers, native haptics.
- **Feel and juice:** `.sensoryFeedback(.success)` on like; fill `.smooth(0.25)`; pop `.spring(response: 0.2, dampingFraction: 0.45)` then settle `.spring(0.4, 0.6)`; burst `easeOut(0.7)`; "+1" sways -6 to +6 degrees while rising.
- **Techniques:** Progress-driven radial particle burst (one 0-to-1 value drives cos/sin offsets, scale, opacity, ring scale) + `withAnimation` completion handlers instead of Timers; `.contentTransition(.symbolEffect(.replace))` on the heart. Already the modern pattern — lift nearly as-is.
- **Lift notes:** No shared dependencies (native `.sensoryFeedback`, in-file palette, SF Symbols). ~211 lines. Difficulty: easy-moderate. Parameterize particle count, burst radius, colors; add an unlike path.
- **Keywords:** like, favorite, heart, burst, particles, plus one, celebration, reaction, spring pop, sensoryFeedback, social

### Add to Cart
- **Path:** `Code/Common/Animations/Cart`
- **Files:** `AddCartView.swift`, `CartView.swift`, `ShirtView.swift`, `SupportShapes/Tick.swift`, `SupportShapes/Triangle.swift`
- **What it shows:** A full-width "Add to cart" pill: the label fades, a cart icon slides in, a checkmark trim-draws with a tilt, a product thumbnail floats up into the cart, then the cart drives off-screen and the button resets.
- **Use when:** E-commerce add-to-cart confirmation that should feel like dispatch and shipping, not a bare checkmark toast.
- **Feel and juice:** Success notification haptic on tap; cart travel `easeIn(0.55).delay(0.25)`; bounce squeeze `.spring(response: 0.25, dampingFraction: 0.85)`; full reset at 2.5s with a zero-duration snap to origin.
- **Techniques:** A cart-state enum encodes x-offset + image + curve, advanced by a Timer chain; custom `Tick` and `Triangle` shapes with `.trim` draws. Replace Timers with `.phaseAnimator`, `UIScreen.main.bounds` with `GeometryReader`, and the shirt asset with the real product thumbnail.
- **Lift notes:** `HapticManager` + 4 image assets. ~370 lines. Difficulty: involved. Parameterize travel offsets, intervals, thumbnail.
- **Keywords:** add to cart, checkout, ecommerce, cart slide, checkmark trim, product fly, confirmation, pill button

### Submit Button (morph to spinner)
- **Path:** `Code/Common/Animations/SubmitView`
- **Files:** `SubmitView.swift`, `Support Shapes/RotatingCircle.swift` (+ shared `Tick` from Cart)
- **What it shows:** A wide "Submit" pill springs into a circle; a white satellite orbits while the button heartbeat-pulses three times; a checkmark trims on; then it springs back to the labeled pill.
- **Use when:** Form submit / async action where the button itself should become the loading indicator (morph, not spinner-beside-label), with a clear success tick before returning to idle.
- **Feel and juice:** Selection haptic on start; morph `.spring(response: 0.56, dampingFraction: 0.9)`; three linear 0.5s pulses; tick `easeOut(0.35)`.
- **Techniques:** Pill-to-circle morph (width 300 to 92, cornerRadius 20 to 46) + offset-orbiting tracker + shared `Tick.trim`. Wire the done flag to real async completion; replace Timers with `Task` + `.phaseAnimator`.
- **Lift notes:** `HapticManager`, `Color.submitColor`, depends on Cart's `Tick` shape. ~210 lines. Difficulty: moderate. Parameterize rotation count, colors, pulse count, success hold.
- **Keywords:** submit, loading morph, spinner orbit, checkmark, form button, processing, pill to circle, success CTA

### Wi-Fi Scanner
- **Path:** `Code/Common/Animations/Wifi`
- **Files:** `WifiView.swift`, `ArcView.swift`, `CircleEmitter.swift` + 2 support shapes
- **What it shows:** Three concentric wifi arcs and a center dot; tap starts "Searching" with bouncing arcs and an expanding ripple; after ~4.2s the arcs turn green "Connected" with a 50-dot staggered particle burst.
- **Use when:** Connection / pairing / device-discovery UX (Wi-Fi, Bluetooth, hardware setup) where searching should feel active and connecting should feel rewarding.
- **Feel and juice:** Medium impact on tap; staggered arc oscillation on a 0.35s base interval; expanding halo `.easeIn` repeatForever; burst particles `easeInOut(0.125).delay(0.01 * index)`.
- **Techniques:** Multi-Timer oscillating offsets on stacked custom arc shapes (220 to 320 degree stroked arcs) + a brief particle emitter; static flags coordinate direction across views (fragile — replace with a phase animator or `TimelineView` when lifting).
- **Lift notes:** `HapticManager`, two wifi palette colors. ~396 lines (one shape file is unused). Difficulty: involved (timer sync). Parameterize durations, radii, connected color; wire to a real connect callback.
- **Keywords:** wifi, scanning, connecting, signal arcs, pairing, network, particle burst, searching, device discovery

### Floating Action Menu
- **Path:** `Code/Common/Animations/AddView`
- **Files:** `AddView.swift`, `ExpandingView.swift`
- **What it shows:** A central plus on a rounded square expands into four SF Symbol action tiles flying out along the cardinal directions while the plus rotates 45 degrees, scales, and fades; tap again collapses.
- **Use when:** Multi-action FAB / compose menus (new note, attach photo, record) where one control must reveal a small set of related actions without opening a sheet.
- **Feel and juice:** Light impact haptic on toggle; hub `.spring(response: 0.35, dampingFraction: 0.85)`; tiles `easeOut(0.25).delay(0.05)` — a short stagger with mild overshoot.
- **Techniques:** Direction-enum offset choreography with counter-rotated icons (container rotates +43 degrees, icon -43 so glyphs stay upright); a single `isAnimating` Bool drives everything via bindings.
- **Lift notes:** `HapticManager`, `Color.background`/`label`, SF Symbols only. ~165 lines. Difficulty: easy. Parameterize symbols, offsets, spring, tile size.
- **Keywords:** FAB, floating action button, expand menu, radial actions, plus to close, compose, speed dial, multi-action

---

## Toggles and switches with identity

### Yin-Yang Theme Toggle
- **Path:** `Code/Common/Animations/YinYang-Toggle`
- **Files:** 4 views + `YinYangViewModel.swift`
- **What it shows:** A capsule theme switch whose yin-yang knob slides and rotates 180 degrees; toggling expands a dark circle ripple (or a white full-screen fill) to rewrite the whole scene light-to-dark. Entrance trim-draws the capsule and symbol with staggered text.
- **Use when:** Branded light/dark theme switcher with personality: onboarding theme pick, settings hero, or any dual-mode toggle that should visibly transform the entire screen.
- **Feel and juice:** Medium impact haptic; knob `.snappy(duration: 0.75)`; background `.smooth` expanding into dark, `.snappy` returning; entrance staggers on ~0.5s multiples.
- **Techniques:** `@Observable` theme flag driving dual `scaleEffect` backgrounds + capsule knob offset/rotation; the ripple is a scaled `Circle` anchored at the toggle. The yin-yang shape uses `UIBezierPath` (hybrid UIKit) — prefer a pure SwiftUI `Path` when lifting; map the flag to real `preferredColorScheme`.
- **Lift notes:** `HapticManager`, `Color.label`/`background`. ~580 lines. Difficulty: involved. Parameterize duration, capsule size, ripple origin; bind to the app theme store.
- **Keywords:** theme switcher, dark mode, capsule toggle, ripple expand, light dark, branded toggle, trim draw, scene transform

### Light Switch (pull-cord bloom)
- **Path:** `Code/Common/Animations/LightSwitch`
- **Files:** `LightSwitchView.swift`
- **What it shows:** A dark scene with a right-edge pull-cord; tap or pull the knob and a yellow circle scales from a flat ellipse below the frame into a full-screen warm bloom. Reverse collapses snappier.
- **Use when:** Dramatic binary state changes that should flood the UI with color — room lights, focus mode, celebration reveal. A one-file, high-drama toggle.
- **Feel and juice:** Medium impact haptic; cord `.spring(dampingFraction: 0.65).speed(1.25)`; drag follows with `.interactiveSpring()`; pull past 100pt commits; bloom `easeIn(0.35)` on, faster `easeOut` off.
- **Techniques:** Non-uniform `scaleEffect` ellipse bloom (xScale 2 / yScale 0.4 collapsed, 4/4 expanded) + top-anchored capsule cord whose height tracks the drag; simultaneous tap + `DragGesture(minimumDistance: 0)`.
- **Lift notes:** `HapticManager`, `Color.background`. Single ~183-line file. Difficulty: easy-moderate. Parameterize bloom color, drag threshold, rail position; replace `UIScreen.main` with geometry.
- **Keywords:** light switch, pull cord, full screen bloom, on off, drag toggle, dramatic lighting, color flood

### Light Bulb (dimmable vector lamp)
- **Path:** `Code/Common/Animations/Light Bulb`
- **Files:** `LightBulbView.swift` + 2 support views + 2 support shapes
- **What it shows:** A hanging vector bulb (wire, screw cap, glass, filament). Power toggles a warm yellow scene flood and glow; while on, an arc slider dims glow and background continuously.
- **Use when:** Settings / smart-home / ambient controls where on-off should feel physical and brightness is continuous — richer than a plain `Toggle` + `Slider` pair.
- **Feel and juice:** Medium impact on power; toggle `.spring(response: 0.3, dampingFraction: 0.6)`; slider knob `.interactiveSpring(duration: 0.3)`; glow radius scales `10 + brightness * 20`; slider enters with `.scale.combined(with: .opacity)`.
- **Techniques:** Geometry-fraction vector bulb (custom Bezier silhouette + filament shapes) + polar arc `DragGesture` mapped through `atan2` (arc 160 to 20 degrees, crossing 360). Includes an iOS 26 `GlassEffectContainer`/`.glassEffect` branch with a material fallback — a live example of pairing custom motion with Liquid Glass.
- **Lift notes:** `HapticManager`, one hex color, SF Symbols. ~466 lines. Difficulty: moderate. Parameterize brightness binding, glow curve; gate the glass branch with `#available(iOS 26.0, *)`.
- **Keywords:** light bulb, brightness, dimmer, curved slider, arc slider, glow, smart home, ambient, Liquid Glass

---

## Cards and gesture-driven browsing

### Auto Scroller (wallet card carousel)
- **Path:** `Code/Common/Animations/Auto Scroller`
- **Files:** `Views/AutoScrollerView.swift`, `ViewModels/AutoScrollerViewModel.swift`, `Models/WalletCard.swift` + 6 card-face support views
- **What it shows:** One wallet-style credit card at a time advances on a 2s timer (or swipe), sliding in from the trailing/leading edge; a pill page indicator stretches for the active index; styled card faces with holder name and masked digits.
- **Use when:** Featured-item carousels that should auto-advance, wallet "pick a card" heroes, onboarding product showcases, endless single-hero decks.
- **Feel and juice:** Auto-advance every 2s via `Timer.publish`; swipe commits at +-100pt; direction-aware asymmetric `.move` transitions inside `withAnimation(.snappy)`; indicator width 18 vs 6.
- **Techniques:** Conditional single-card render + asymmetric `.move` transition (only the current index exists in the tree); `DragGesture` threshold; modular index wrap; `@Observable` ViewModel. Pre-iOS-17 pattern — consider `scrollPosition` + `scrollTargetBehavior(.paging)` on modern targets.
- **Lift notes:** ClashGrotesk fonts, `Color(hex:)`, 3 provider logo assets. ~9 files / ~450 lines. Difficulty: easy-moderate. Parameterize interval, threshold, card list, aspect ratio.
- **Keywords:** auto carousel, timer advance, wallet cards, page indicator, swipe, asymmetric transition, featured items, infinite loop

### Bank Card (flip + snap carousel)
- **Path:** `Code/Common/Animations/Bank Card`
- **Files:** `CardView.swift`, `CardFrontView.swift`, `CardBackView.swift` + models + `SnapCarousel.swift`
- **What it shows:** A horizontal snap carousel of bank cards under a live balance header; tap flips the active card in 3D to reveal the mag-stripe/CVV back; swiping changes card, resets the flip, and animates the balance.
- **Use when:** Wallet/payment UI, "view CVV" security reveals, multi-card account pickers — anywhere the physical-card metaphor earns trust.
- **Feel and juice:** Flip `.spring(response: 0.45, dampingFraction: 0.75)` toggling 0-to-180 with `perspective: 0.5`; light haptic on tap, medium on carousel snap; snap threshold +-50pt; face swap via opacity at halfway (the back is pre-rotated 180 so text is never mirrored).
- **Techniques:** Custom HStack offset carousel (drag translation feeds a rubber-band offset; release clamps index) + `rotation3DEffect` Y-flip in a `ZStack`. Legacy carousel math — replace with iOS 17 scroll APIs on modern targets; keep the flip.
- **Lift notes:** `HapticManager`, 2 image assets, a `Double.clean` helper. ~7 files / ~550 lines. Difficulty: involved. Parameterize palette, snap threshold, perspective, card width (0.85x screen, ISO-ish ratio width/1.593).
- **Keywords:** card flip, 3D rotation, CVV reveal, snap carousel, wallet balance, perspective, haptic snap, payment UI

### Cards Shuffle (drag to back of deck)
- **Path:** `Code/Common/Animations/Cards Shuffle`
- **Files:** `CardsShuffleView.swift`
- **What it shows:** A short deck stacked with fake depth (smaller, lifted cards behind); drag the front card up past a threshold and it springs to the back while the rest promote forward; short drags spring back.
- **Use when:** Story/album stacks, next-item browsing without full swipe-away, photo or product decks, playful onboarding card stacks.
- **Feel and juice:** Depth from `scaleStep = 0.05` and `depthSpacing = -16` per level; commit at drag height < -60; snap-back `.spring(response: 0.8, dampingFraction: 0.7)`; reorder `.spring(0.7, 0.75)`.
- **Techniques:** ZStack depth stack + `removeLast`/`insert(at: 0)` spring reorder; `DragGesture` only on the top index; `zIndex` = array index; continuous finger-follow then animated array mutation. Single file, no ScrollView.
- **Lift notes:** `Color.background` only. ~160 lines. Difficulty: easy. Parameterize colors, scale/depth/threshold, card size, content.
- **Keywords:** card stack, shuffle to back, drag threshold, depth scale, spring snapback, deck browse, zIndex promote

### Cards Swap (wallet pile cycle + fan)
- **Path:** `Code/Common/Animations/Cards Swap`
- **Files:** `Views/CardSwapView.swift`, `ViewModels/CardSwapViewModel.swift` + models + 2 support views
- **What it shows:** A wallet screen with stacked credit cards peeking via negative Y offsets; drag the top card up/down past 120pt to cycle it to the bottom; a toolbar button toggles stacked vs expanded fan with a bouncing SF Symbol.
- **Use when:** Digital wallet home, multi-card selector, "cards in a pile" finance UX with an expand-to-browse mode.
- **Feel and juice:** Live drag follows with `.smooth` (up) vs `.snappy` (down); commit `easeInOut(0.5)`; reset `.snappy(0.35)`; stack/expand `.smooth` + `.symbolEffect(.bounce.byLayer, speed: 1.2)`.
- **Techniques:** Negative-Y wallet stack + top-card vertical drag mapped to an array rotate; `zIndex(10 + ix)`; only the last index accepts the drag while stacked; `@Observable` ViewModel; modern curves throughout (iOS 17+ friendly).
- **Lift notes:** ClashGrotesk fonts, provider image assets, `UIScreen` width. ~5 files / ~400 lines. Difficulty: moderate. Parameterize threshold, ratio, gradients, card count.
- **Keywords:** wallet stack, card swap, drag cycle, fan expand, snappy smooth, symbolEffect bounce, pile overlap

---

## Text and hero moments

### Text Bouncing (touch-scrub headline)
- **Path:** `Code/Common/Animations/Text Bouncing`
- **Files:** `Views/TextBouncingView.swift`, `Views/Support Views/BouncingCharacterView.swift`
- **What it shows:** A large headline split into per-character views; dragging a finger across the line makes each letter under the touch pop up (scale 1.4, lift -20, tint blue) with neighbors tinting lighter, plus a light haptic per character change.
- **Use when:** Playful onboarding/hero titles, name personalization, marketing headlines, celebration copy — anywhere touching the words should feel rewarding.
- **Feel and juice:** `.smooth(duration: 0.225)` on the active index; light impact haptic when the index changes; phrase shuffle `.snappy(0.3)` + selection haptic; text swap `.contentTransition(.numericText())`.
- **Techniques:** PreferenceKey-published character frames + `DragGesture` x-to-index hit-test in a named coordinate space; `HStack(spacing: 0)` of per-character views; `minimumDistance: 0` enables tap-scrub. Modern pattern.
- **Lift notes:** `HapticManager`, ClashGrotesk 48pt. ~190 lines. Difficulty: easy-moderate. Parameterize scale/offset/colors, font, phrase list. `ForEach` id is character offset — keep `.id(currentText)` when text changes.
- **Keywords:** bouncing letters, per-character, drag scrub, haptic text, onboarding hero, interactive typography, touch the words

### TextSwirl (word ring scatter)
- **Path:** `Code/Common/Animations/TextSwirl`
- **Files:** `TextSwirlView.swift`
- **What it shows:** Dozens of words arranged as spokes on a circular ring; tap scatters them chaotically with random rotation/offset/scale while a random keyword settles in the center; reset snaps them back to the neat circle.
- **Use when:** Playful brand/word-cloud heroes, "pick a vibe" or random-highlight moments, exploratory tag clouds with a featured word.
- **Feel and juice:** Appear `.smooth(1)` from 45 degrees; scatter `.bouncy(duration: 2)`; ring rotation `easeInOut(3)`; reset `.snappy(2)`; center keyword `.contentTransition(.numericText())`.
- **Techniques:** `matchedGeometryEffect` between the circle layout and the random scatter — the load-bearing trick; per-index rotation `index/count * 360`; iOS 18 `.symbolEffect(.rotate.counterClockwise)` on the reset button with fallback. Random values re-roll inside `body` while scattered (intentional chaos, but know it when lifting).
- **Lift notes:** ClashGrotesk, `Color.label`. ~200 lines single file. Difficulty: moderate. Parameterize word list, durations, highlight color; two unused helper functions remain in the file.
- **Keywords:** word cloud, matchedGeometryEffect, circular layout, scatter, bouncy, random keyword, tag ring, playful hero

### Animated Login (auth-to-welcome sequence)
- **Path:** `Code/Common/Animations/LoginView`
- **Files:** `LoginView.swift` + 5 support shapes
- **What it shows:** A branded login: a bolt icon trim-draws in and a CTA slides up; on tap the button squeezes and exits, a gradient arc orbits a circular profile that spring-scales in with a greeting and twinkling plus-particles; the scene then blurs as a handoff transition.
- **Use when:** Auth/onboarding success sequences, "sign in, then welcome" brand moments, splash-to-home handoffs.
- **Feel and juice:** Bolt `.trim` draw 0.7s `easeOut`; tap squeeze `.spring(0.25, 0.85)`; orbit period 3s; profile `.spring()` at t=3s; seven particles with 0.075-0.225s staggers; exit blur radius 6.
- **Techniques:** Multi-phase Timer choreography + `Shape.trim` stroke draw + `Circle.trim` orbit + particle field. Heaviest Timer choreography in the catalog — modernize with `.phaseAnimator`/`.keyframeAnimator` or async sequences; borrows Cart's `Triangle` shape cross-folder; replace the fake blur exit with real navigation.
- **Lift notes:** `HapticManager`, gradient colors, 2 image assets. ~550 lines total. Difficulty: involved. Parameterize timings, particle layout, brand assets.
- **Keywords:** login animation, sign in, welcome sequence, trim draw, orbit arc, particle twinkle, onboarding choreography, brand auth

---

## Input chrome

### ChatBar (attachment composer)
- **Path:** `Code/Common/Animations/ChatBar`
- **Files:** `ChatBarView.swift`, `AttachmentButton.swift`
- **What it shows:** A pill chat composer; tapping the plus rotates it toward an X, attachment icons (camera/video/contact) rotate and slide in while the text field rotates out, and the whole bar wiggles; after 0.5s the panel auto-collapses.
- **Use when:** Messaging input chrome, attachment overflow without a sheet, playful chat UX.
- **Feel and juice:** Attachment icons `.spring()` from 90 degrees / y+72 to rest; the bar wiggle uses `.interpolatingSpring(mass: 2, stiffness: 14, damping: 10, initialVelocity: 5).delay(0.1)` — the physical shudder is the signature; light haptic per button.
- **Techniques:** Coordinated rotation choreography on shared state (two Bools drive icon rotation, field rotation, and bar tilt) with `rotationEffect` anchored at `.zero`/`.leading`; Timer auto-dismiss. Replace the Timer with `Task.sleep` when lifting.
- **Lift notes:** `HapticManager`, 4 palette colors. ~170 lines. Difficulty: easy-moderate. Parameterize icons, durations, spring params, bar height.
- **Keywords:** chat input, attachment menu, plus to x, spring rotate, bar wiggle, interpolating spring, composer, media attach

---

## Reveals and brand delight

### Scratch to Reveal
- **Path:** `Code/Common/Animations/Scratch to Reveal`
- **Files:** `RevealView.swift`
- **What it shows:** A dark gradient cover over a full-bleed image; dragging paints soft circular holes that reveal the image; strokes auto-fade after 0.25s unless fading is paused; reset clears points with a micro-stagger.
- **Use when:** Scratch-card promos, unlock/reveal rewards, lottery or coupon UX, "wipe to see" spoilers, playful photo reveals.
- **Feel and juice:** Soft 35pt brush via radial gradient stops white-to-clear; ephemeral strokes (fade window 0.25s) make it feel alive; toolbar toggles use `.snappy`/`.smooth` + `.symbolEffect(.bounce)`.
- **Techniques:** `Image.mask { Canvas { ... } }` where the Canvas fills radial-gradient ellipses at drag sample points — the load-bearing trick; `DragGesture(minimumDistance: 0)` appends timestamped points; a timer culls expired points; stopping the timer gives persistent scratch mode.
- **Lift notes:** One image asset. ~193 lines. Difficulty: moderate. Parameterize radius, fade duration, cover view, persist-vs-fade.
- **Keywords:** scratch off, reveal mask, Canvas, radial gradient brush, unlock reward, coupon, drag reveal, spoiler cover

### Octocat Wink (mascot idle + easter egg)
- **Path:** `Code/Common/Animations/Octocat-Wink`
- **Files:** `OctocatView.swift`, `Support Shapes/OctocatLoader.swift`, `Support Shapes/OctoHead.swift`
- **What it shows:** A mascot silhouette as a dim track with a bright trimmed stroke traveling the outline; when a lap completes, one eye randomly squishes into a wink.
- **Use when:** Brand mascot easter eggs, loading/idle ornaments, "alive logo" moments. The wink-on-completion beat generalizes to any mascot.
- **Feel and juice:** Timer every 0.4s advances the stroke by a random 0.075-0.115 step (organic pacing); segment length 0.25; wink is a non-uniform `scaleEffect` (eye height to 0.225) with `easeInOut(0.3)`, random left/right.
- **Techniques:** Traveling `.trim` window on a custom Shape + non-uniform scale wink; eye paths positioned relative to `GeometryReader` mid.
- **Lift notes:** `Color.background`/`label`; heavy Bezier path data is the porting cost. ~320 lines. Difficulty: moderate. Swap the shape for another mascot; parameterize wink timing, stroke width.
- **Keywords:** mascot, wink, stroke trim, travelling path, logo idle, brand easter egg, eye squash, alive logo

---

## Metal shader effects (all iOS 17+)

### Burn Effect
- **Path:** `Code/Common/Shaders/Burn`
- **Files:** `BurnEffect.swift`, `BurnEffect.metal`
- **What it shows:** A view char-burns away bottom-up with a jagged FBM-noise edge glowing orange to yellow-white along the fireline as content turns transparent.
- **Use when:** Delete/destroy transitions, send-to-trash, irreversible confirmations, dramatic card dismissal — "this content is gone forever" moments.
- **Feel and juice:** The edge is organic noise, not a hard wipe; an ember band reads as heat; animatable `progress` plus `TimelineView` time keeps the flame line alive mid-transition.
- **Techniques:** Reusable `.burnEffect(progress:)` modifier wrapping `visualEffect` + `layerEffect(ShaderLibrary.burnEffect(size, progress, time))`; the kernel thresholds `uv.y + fbm(uv*8 + time)` against progress and returns fringe colors or transparent.
- **Lift notes:** Copy both files. Difficulty: moderate (the modifier is reusable; a leftover `SizePreferenceKey` is dead code). Parameterize noise scale, ember band widths/colors, progress curve.
- **Keywords:** burn, fire edge, FBM noise, destroy transition, layerEffect, ember glow, dissolve, incinerate

### Ember Reveal
- **Path:** `Code/Common/Shaders/EmberReveal`
- **Files:** `EmberReveal.swift`, `EmberReveal.metal`
- **What it shows:** An image burns into existence center-out with a noisy circular mask and a bright orange additive burning edge.
- **Use when:** Hero image / unlock / prize-reveal moments, onboarding media intros, gesture-free scratch-adjacent reveals, featured-asset splashes.
- **Feel and juice:** Center-out + value noise feels like paper catching fire rather than a radial wipe; a single 0-to-1 progress over ~5s `.smooth` drives everything.
- **Techniques:** `GeometryReader`-sized `.layerEffect(ShaderLibrary.emberReveal(progress, size))`; the kernel combines center distance + value noise into a threshold with an orange-boosted edge band.
- **Lift notes:** Copy both files + supply an image. Difficulty: easy-moderate — must pass the real rendered size (a hardcoded size breaks the reveal). Parameterize noise scale, edge width, ember color, duration.
- **Keywords:** ember reveal, center-out, burn-in, value noise, image reveal, unlock, hero intro, progress mask

### Chromatic Aberration
- **Path:** `Code/Common/Shaders/ChromaticAberration`
- **Files:** `ChromaticAberrationView.swift`, `ChromaticAberration.metal`
- **What it shows:** A radial RGB channel split from the image center (red pushed out, blue pulled in) with a soft iridescent fringe; tap springs the strength between 0 and 30.
- **Use when:** Holographic or premium photo treatments, lens-flare branding, sci-fi accents, short impact-hit flashes on media.
- **Feel and juice:** Radial distance falloff plus a continuous `sin(time * 2.4)` pulse so the fringe breathes even when idle.
- **Techniques:** `.layerEffect(ShaderLibrary.chromaticAberration(size, strength, time), maxSampleOffset: 50)` inside `TimelineView(.animation)`; the kernel samples R/G/B at radially scaled offsets.
- **Lift notes:** Copy both files, swap the demo image. Difficulty: easy. Parameterize strength, pulse rate, offset ratio.
- **Keywords:** chromatic aberration, RGB split, prism, holographic, lens fringe, photo filter, iridescent, impact flash

### Glitch Effect
- **Path:** `Code/Common/Shaders/GlitchEffect`
- **Files:** `GlitchEffectView.swift`, `GlitchEffect.metal`
- **What it shows:** Digital corruption: horizontal bands randomly shift, RGB splits inside active bands, sparse scan-line flashes and grain; tap spikes intensity to 1 then ease-outs over 2s.
- **Use when:** Error or failure states, "system compromised" branding, cyberpunk marketing beats, punchy retry feedback on a media card.
- **Feel and juice:** Updates are quantized into chunky ticks (`floor(time * 14)`) so it feels hardware-broken, not smoothed; intensity gates band count and shift magnitude.
- **Techniques:** `TimelineView` + `.layerEffect(ShaderLibrary.glitchEffect(size, time, intensity))`; the kernel hashes per band/tick for shifts, RGB split, flash lines, and grain.
- **Lift notes:** Copy both files + an image. Difficulty: moderate. Parameterize band height, tick rate, max shift, intensity decay.
- **Keywords:** glitch, RGB split, scanline, band shift, digital corruption, cyberpunk, error state, intensity decay

### Halftone
- **Path:** `Code/Common/Shaders/Halftone`
- **Files:** `HalftoneView.swift`, `Halftone.metal`
- **What it shows:** Newspaper-print treatment: luminance-sized circular ink dots on warm cream paper, blended in via a 0-to-1 progress with a soft spring toggle.
- **Use when:** Print/editorial photo filters, publish or print-preview transitions, nostalgic media treatments, toggleable style modes in a camera or gallery app.
- **Feel and juice:** Smoothstep anti-aliased dots and BT.709 luminance mapping feel intentional; the juice is the slow spring morph between photo and print (no time uniform).
- **Techniques:** `.layerEffect(ShaderLibrary.halftone(size, dotSize, progress))` with no TimelineView; the kernel snaps to a cell grid and sizes dots by inverted luma.
- **Lift notes:** Copy both files + an image. Difficulty: easy. Parameterize dot size (demo 8), ink/paper colors, spring.
- **Keywords:** halftone, newspaper dots, print filter, luminance, editorial, ink paper, photo style, retro print

### Pixel Snap
- **Path:** `Code/Common/Shaders/Pixel Snap`
- **Files:** `PixelSnapView.swift`, `PixelSnap.metal`
- **What it shows:** Content starts as huge blocky pixels and snaps into the sharp image as progress goes 0 to 1, fading in opacity along the way.
- **Use when:** Asset load-in, materialize/unlock reveals, retro-game intros, low-res-to-hi-res loading metaphors, sticker or emoji appear moments.
- **Feel and juice:** Quadratic pixel-size curve (`1 + (1-p)^2 * 50`) eases from ~50px blocks so the final sharpen feels snappy.
- **Techniques:** `.layerEffect(ShaderLibrary.pixelSnap(progress, size))`; the kernel floors positions into blocks and samples block centers.
- **Lift notes:** Copy both files. Difficulty: easy. Fix on lift: the demo passes a hardcoded `CGSize(350, 300)` while the frame is 350x400 — pass the real size. Parameterize max block size and easing.
- **Keywords:** pixelate, pixel snap, blocky reveal, materialize, mosaic, retro, load-in, fade-in clarify

### Wave Ripple
- **Path:** `Code/Common/Shaders/RippleEffect`
- **Files:** `RippleEffectView.swift`, `RippleEffect.metal`
- **What it shows:** A water-like ripple ring expands from the tap location, distorting the image along the wavefront then decaying.
- **Use when:** Touch feedback on images and cards, drop-a-pebble delight, subtle success confirmation on a hero image. The most interactive shader in the set — the origin follows the touch.
- **Feel and juice:** Gaussian envelope on the expanding front + time-phased sine + amplitude decay as progress completes; ~1.6s per ripple.
- **Techniques:** The only entry using `.distortionEffect(ShaderLibrary.waveRipple(size, touchPoint, time, progress), maxSampleOffset: 20)` in a `TimelineView`; the `float2` kernel returns positions offset by radial sine displacement.
- **Lift notes:** Copy both files + an image. Difficulty: moderate — gesture-to-image coordinate mapping needs care (the demo offsets Y by +40). Parameterize speed, frequency, amplitude, duration.
- **Keywords:** ripple, wave, distortionEffect, touch location, water, tap feedback, wavefront, physical touch

---

## Shared infrastructure

What the demo app provides that lifted code must replace or bring along:

- **`HapticManager`** (`Code/Services/HapticManager.swift`): a small UIKit wrapper — `makeNotifiationFeedback(.success|.info|.failure)`, `makeSelectionFeedback()`, `makeImpactFeedback(.light|.medium|.heavy)`. On iOS 17+ replace call sites with SwiftUI's `.sensoryFeedback` (the Like entry shows the modern pattern).
- **`Colors.swift`** (`Code/Utils/Colors.swift`): `Color.background`, `Color.label`, many per-demo statics (`chatBackground`, `submitColor`, `pillColor`, wifi colors, circle gradients), plus `Color(hex:)` and `Color(r:g:b:)` helpers. Map to your app palette or system colors.
- **`FontManager` / ClashGrotesk**: card and text demos use the custom ClashGrotesk family. Swap to your app fonts; only the entries that mention it depend on it.
- **Image assets:** Cart (cart, shirt), Bank Card (axis, visa), Auto Scroller (provider logos), Login (face, medium), Scratch/shaders (photos). Bring or substitute.
- **Registration/routing in the demo:** `AnimationItem.all` + `AnimationDestination` (Home tab) and `ShaderItem.all` + `ShaderDestination` (Shaders tab) via a `Router<Destination>`/`NavigationPath`. Irrelevant when lifting a single animation; relevant when contributing back upstream.
- **Screen sizing:** several entries hardcode `UIScreen.main.bounds`; prefer `GeometryReader` or container-relative sizing when lifting.

## Recurring motion vocabulary in this source

- **Timer-scheduled phase state machines** dominate older entries (`onAppear` -> nested `Timer` + `withAnimation`). Keep the geometry and timings; move the sequencing to `.phaseAnimator`, `.keyframeAnimator`, `withAnimation` completion handlers, or `Task.sleep`.
- **`Shape` + `.trim(from:to:)`** is the signature drawing trick: traveling stroke windows (Octocat, Github, Infinity), draw-on checkmarks (`Tick`, tick shapes), arc progress (CircleLoader, Submit orbit), and entrance trim-draws (Login bolt, YinYang capsule).
- **Drag-threshold commit grammar:** drags follow the finger live, then commit past a threshold (Bank Card +-50pt, Cards Shuffle -60pt, Auto Scroller +-100pt, Cards Swap +-120pt, LightSwitch 100pt) and settle with a spring or `.snappy`.
- **Haptics pair with commitment, not motion:** impact on toggles/taps, selection on picker-like changes, notification-success on completed actions. Newer entries use `.sensoryFeedback`; older ones use `HapticManager`.
- **Modern Apple curves in newer entries:** `.snappy`, `.smooth`, `.bouncy`, `.symbolEffect`, `.contentTransition(.numericText())` — these are the defaults to keep. Older `easeInOut` + Timer entries are the ones to modernize.
- **Depth tricks by family:** zIndex + scale/offset stacks (card decks), `rotation3DEffect` with perspective (flips, cube loader), mask/Canvas (scratch reveal), Metal `layerEffect`/`distortionEffect` (shaders).

## Lift checklist

After adapting any entry into an app:

1. Swap `HapticManager` calls for `.sensoryFeedback` (or confirm the wrapper is wanted).
2. Replace `Color.*` statics and ClashGrotesk fonts with the app's design tokens.
3. Replace `UIScreen.main.bounds` with `GeometryReader` / container sizing.
4. Convert Timer state machines to `.phaseAnimator` / `.keyframeAnimator` / `withAnimation` completions unless the target OS forbids it.
5. Wire demo timers that fake progress/completion to real async work.
6. Honor Reduce Motion: gate large movement behind `@Environment(\.accessibilityReduceMotion)` with a crossfade fallback.
7. Build, run, and watch it in motion (Simulator or Previews) — motion cannot be judged from code.
