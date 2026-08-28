# Adding a Source

The repeatable recipe for turning a new animation repo (or a refresh of an
existing one) into a catalog file this skill can match against. Follow it
whenever the user says "add this animation repo to the skill" or sends a
link to more cool patterns.

The output contract is fixed so every catalog reads the same way: one
`references/catalog-<owner>-<repo>.md` per source, entries grouped by
interaction moment, each entry in the standard block format below.

## Contents

- 1. Stage the source
- 2. Survey and slice
- 3. The entry block format
- 4. Assemble the catalog file
- 5. Register the source
- 6. Verify before shipping
- Refreshing an existing source

## 1. Stage the source

```bash
git clone --depth 1 <repo-url> /tmp/<repo-name>
cd /tmp/<repo-name> && git log -1 --format='%H %cs'   # pin the commit
```

A depth-1 clone is enough for a first cataloging pass (you only read the
tip you are pinning). It is NOT enough to check out or diff against an
older pinned commit later — see the refresh section for how to fetch
history first.

Record the license (lifting code from an unlicensed or restrictively
licensed repo is a real problem — surface it to the user before cataloging)
and the deployment target if discoverable (project file, README).

## 2. Survey and slice

List the animation folders/files. If the source has more than ~8 distinct
animations, fan out parallel read-only subagents (if the environment has a
Task/subagent tool; with the `waves` skill installed, run it as a wave).
Slice by folder groups of roughly 7-10 animations per worker so each worker
reads every file in its slice. Fewer than ~8: read them yourself.

Give each worker: the exact folder list, the entry block format from
section 3, and these rules:

- Base every claim on code actually read; never guess from folder names.
- Name the load-bearing technique first (the one trick that makes the
  animation work).
- Quote notable literal values (spring response/damping, durations,
  thresholds) — they are the feel.
- Flag old patterns a modern agent should replace (Timer state machines,
  deprecated `.animation(_:)` without value, UIKit haptic wrappers,
  hardcoded screen bounds) and iOS-version-sensitive APIs.
- Report external dependencies: shared color/font/haptic helpers, image
  assets, cross-folder shape imports.
- End with group observations: recurring conventions across the slice.

One extra worker should read the shared infrastructure (haptics, colors,
fonts, routing/registration) so the catalog's "Shared infrastructure"
section is accurate.

## 3. The entry block format

Every animation gets exactly this block:

```markdown
### <Human-readable name>
- **Path:** `<path within the source repo>`
- **Files:** <file names, including subfolders>
- **What it shows:** <1-2 sentences: visual + motion, from code>
- **Use when:** <specific product/UX moments this fits; opinionated>
- **Feel and juice:** <springs, easing, stagger, haptics, thresholds, with notable literal values>
- **Techniques:** <load-bearing trick first, then the precise APIs>
- **Lift notes:** <dependencies, approximate size, difficulty easy/moderate/involved, what to parameterize, bugs or dead code to fix on lift>
- **Keywords:** <8-15 comma-separated search terms>
```

Difficulty scale: **easy** = single file, few dependencies, lift mostly
as-is; **moderate** = a few files or one heavy dependency (e.g. a large
custom path); **involved** = multi-view orchestration, timer choreography
to modernize, or fragile coordination.

## 4. Assemble the catalog file

Create `references/catalog-<owner>-<repo>.md` with:

1. **Header:** source URL, pinned commit + analysis date, license,
   deployment floor, coverage counts, a pointer to read source before
   lifting.
2. **Entries grouped by interaction moment**, using the existing group
   names where they fit (Wait states; Progress with a real percentage;
   Action feedback and confirmation; Toggles and switches with identity;
   Cards and gesture-driven browsing; Text and hero moments; Input chrome;
   Reveals and brand delight; Metal shader effects). Add a new group only
   when nothing fits; if you add one, also add it to the SKILL.md mode
   picker and the matching-playbook taxonomy.
3. **Shared infrastructure:** what the source's demo app provides that
   lifted code must replace (helpers, palettes, fonts, assets, routing).
4. **Recurring motion vocabulary:** the source's signature tricks and
   conventions, so an agent absorbing the catalog learns the style, not
   just the inventory.
5. **Lift checklist:** the source-specific adaptation steps.

## 5. Register the source

1. Add the source to `sources.md` (repo, catalog link, pinned commit,
   license, scope, author).
2. Add a row to the Catalogs table in `SKILL.md`.
3. If new interaction groups were created, update the SKILL.md mode picker
   and the taxonomy in `matching-playbook.md`.

## 6. Verify before shipping

- Spot-check at least 3 random entries against the actual source files:
  paths resolve at the pinned commit, technique claims match the code,
  literal values are real.
- Confirm every relative link in the new/updated files resolves.
- Confirm the catalog states license and pinned commit.
- If this repo has validators (e.g. `scripts/validate-skill-metadata.py`),
  run them.

## Refreshing an existing source

Same flow, scoped — but a refresh needs the pinned commit in local
history, which a depth-1 clone does not have. Stage with history first:

```bash
git clone <repo-url> /tmp/<repo-name>          # full clone, or:
git -C /tmp/<repo-name> fetch --unshallow      # if a shallow clone already exists
git -C /tmp/<repo-name> cat-file -e <pinned>^{commit}   # confirm the pin is present
```

(A targeted `git fetch origin <pinned> --depth 1` also works on hosts that
allow fetching reachable commits by SHA — GitHub does — but it only makes
the pin checkoutable; the range diff below still needs the connected
history that a full clone or `--unshallow` provides.)

Then diff the repo between the pinned commit and HEAD
(`git log --stat <pinned>..HEAD`), analyze only added/changed animation
folders, append or update entries, and bump the pinned commit + date in
both the catalog header and `sources.md`.

If the pinned commit is missing even after fetching history (force-pushed
away or the repo was re-created), note that in `sources.md` and re-catalog
from the current tip instead of diffing.
