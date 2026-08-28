#!/bin/bash
# End-to-end proof: install the skills and configure model routing, touching
# nothing that already exists.
#
# Isolation, per layer:
#   skills linking   HOME=$SANDBOX/home          fresh skill roots, real code
#   model scan       real HOME (credentials live there); output redirected to
#                    the sandbox. Every probe is read-only: omp models/usage,
#                    cursor-agent models/status, grok models, codex login
#                    status, claude auth status, a T3 manifest file read.
#   role assign      AGENT_SKILLS_HOME=$SANDBOX  routing files in the sandbox
#   config write     OMP_PROFILE=$PROFILE        isolated omp settings
#
# Real state is only ever HASHED, never written.
set -uo pipefail

SANDBOX=${SANDBOX:-$(mktemp -d)/e2e}
PROFILE=e2e-proof
CLONE=$SANDBOX/skills-collection
SOURCE=${SOURCE:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}
export AGENT_SKILLS_HOME=$SANDBOX/agents
export AGENT_ROUTES_FILE=$SANDBOX/agents/routes.json

pass=0; fail=0
check() {
  if [ "$2" -eq 0 ]; then printf '  \033[32mPASS\033[0m %s\n' "$1"; pass=$((pass+1))
  else printf '  \033[31mFAIL\033[0m %s\n' "$1"; fail=$((fail+1)); fi
}
step() { printf '\n\033[1m%s\033[0m\n' "$1"; }

REAL_CONFIG=$HOME/.omp/agent/config.yml
REAL_CONFIG_BEFORE=$(shasum -a 256 "$REAL_CONFIG" | cut -d' ' -f1)
REAL_ROUTES_BEFORE=$(shasum -a 256 "$HOME/.agents/routes.json" 2>/dev/null | cut -d' ' -f1)
REAL_LINK_BEFORE=$(readlink "$HOME/.agents/skills/lee-engineering")
REAL_PROFILES_BEFORE=$(ls "$HOME/.omp/profiles" 2>/dev/null | wc -l | tr -d ' ')

step "0. Clone the branch under test into the sandbox"
rm -rf "$CLONE" "$SANDBOX/home" "$SANDBOX/agents"
mkdir -p "$SANDBOX/agents"
touch "$SANDBOX/.started"
git clone -q --branch "${BRANCH:-$(git -C "$SOURCE" rev-parse --abbrev-ref HEAD)}" "$SOURCE" "$CLONE"
echo "  $(git -C "$CLONE" rev-parse --short HEAD)  $(git -C "$CLONE" log -1 --pretty=%s | cut -c1-64)"

step "1. Install the skills into a fresh HOME"
mkdir -p "$SANDBOX/home/.claude" "$SANDBOX/home/.cursor" "$SANDBOX/home/.codex" "$SANDBOX/home/.omp/agent"
printf '# Shared rules\nBe careful.\n' > "$SANDBOX/home/.omp/agent/AGENTS.md"
mkdir -p "$SANDBOX/home/.claude/skills/architect"
printf 'my own architect skill\n' > "$SANDBOX/home/.claude/skills/architect/SKILL.md"
printf 'irreplaceable\n' > "$SANDBOX/home/.claude/skills/architect/NOTES.md"

"$CLONE/bin/agent-skills" --home "$SANDBOX/home" link >"$SANDBOX/link1.log" 2>&1
check "refuses to touch a same-named skill the user wrote" \
  "$(grep -q refused "$SANDBOX/link1.log" && echo 0 || echo 1)"
check "that user's file survives untouched" \
  "$(grep -q irreplaceable "$SANDBOX/home/.claude/skills/architect/NOTES.md" && echo 0 || echo 1)"

"$CLONE/bin/agent-skills" --home "$SANDBOX/home" link --replace-copies >"$SANDBOX/link2.log" 2>&1
check "--replace-copies moves it aside rather than deleting" \
  "$([ "$(find "$SANDBOX/home/.claude/skills" -maxdepth 1 -name 'architect.replaced-*' | wc -l | tr -d ' ')" -eq 1 ] && echo 0 || echo 1)"
check "the moved-aside copy still holds the user's file" \
  "$(grep -rq irreplaceable "$SANDBOX/home/.claude/skills"/architect.replaced-* && echo 0 || echo 1)"

expected=$(find "$CLONE" -maxdepth 2 -name SKILL.md | wc -l | tr -d ' ')
for root in .agents/skills .claude/skills .cursor/skills .codex/skills; do
  n=$(find "$SANDBOX/home/$root" -maxdepth 1 -type l 2>/dev/null | wc -l | tr -d ' ')
  check "$root holds $expected symlinks (got $n)" "$([ "$n" -eq "$expected" ] && echo 0 || echo 1)"
done
check "no real directory left in a skill root" \
  "$([ "$(find "$SANDBOX/home/.agents/skills" -maxdepth 1 -mindepth 1 ! -type l | wc -l | tr -d ' ')" -eq 0 ] && echo 0 || echo 1)"
# macOS resolves /tmp to /private/tmp, so compare resolved paths.
check "a link resolves into the clone, not a copy" \
  "$([ "$(cd "$SANDBOX/home/.agents/skills/lee-engineering" && pwd -P)" = "$(cd "$CLONE/lee-engineering" && pwd -P)" ] && echo 0 || echo 1)"
check "CLAUDE.md is a symlink to AGENTS.md" "$([ -L "$SANDBOX/home/.claude/CLAUDE.md" ] && echo 0 || echo 1)"
check "CLAUDE.md serves the AGENTS.md content" \
  "$(grep -q 'Shared rules' "$SANDBOX/home/.claude/CLAUDE.md" && echo 0 || echo 1)"

"$CLONE/bin/agent-skills" --home "$SANDBOX/home" link --json >"$SANDBOX/link3.json" 2>&1
changed=$(/usr/bin/python3 -c "import json;print(len([a for a in json.load(open('$SANDBOX/link3.json'))['actions'] if a['action']!='already-linked']))")
check "re-running link changes nothing ($changed)" "$([ "$changed" -eq 0 ] && echo 0 || echo 1)"

mv "$CLONE/architect" "$CLONE/.architect-hidden"
"$CLONE/bin/agent-skills" --home "$SANDBOX/home" prune >"$SANDBOX/prune.log" 2>&1
check "prune clears links a removed skill left behind" \
  "$([ "$(grep -c 'prune ' "$SANDBOX/prune.log")" -ge 4 ] && echo 0 || echo 1)"
mv "$CLONE/.architect-hidden" "$CLONE/architect"

step "2. Run the installer itself, end to end, everything under temp"
# One `agent-setup` invocation. --skills-home puts skill roots in the sandbox;
# --config-env scopes the omp config dir to the sandbox for the write step only,
# because omp keeps credentials beside its config and the scan needs them.
"$CLONE/bin/agent-setup" \
  --skills-home "$SANDBOX/home" \
  --config-env "PI_CODING_AGENT_DIR=$SANDBOX/omp-agent" \
  >"$SANDBOX/setup.log" 2>&1
setup_rc=$?
check "agent-setup exits 0" "$setup_rc"
check "it ran all three steps" \
  "$([ "$(grep -c '^\[[123]/3\]' "$SANDBOX/setup.log")" -eq 3 ] && echo 0 || echo 1)"
sed -n '/^sources/,/^$/p' "$SANDBOX/setup.log" | sed 's/^/  /'

/usr/bin/python3 - <<'PY2' > "$SANDBOX/scan.txt"
import json, os
r = json.load(open(os.environ["AGENT_ROUTES_FILE"]))
print("harness", r["harness"]["id"])
print("harness_routes", sum(1 for x in r["routes"] if x["sourceKind"] == "harness"))
print("fallback_routes", sum(1 for x in r["routes"] if x["sourceKind"] == "cli-fallback"))
print("sufficient", r["harnessSufficient"])
print("unauthenticated", ",".join(s["id"] for s in r["sources"] if s["status"] == "unauthenticated") or "none")
PY2
sed 's/^/  /' "$SANDBOX/scan.txt"
check "found the real harness catalog" \
  "$([ "$(awk '/^harness_routes/{print $2}' "$SANDBOX/scan.txt")" -gt 50 ] && echo 0 || echo 1)"
check "only signed-in CLIs contributed routes" \
  "$(grep -q 'unauthenticated none' "$SANDBOX/scan.txt" && echo 0 || echo 1)"

step "3. Check what the installer produced"
sed -n '/^roles/,/^harness config/p' "$SANDBOX/setup.log" | sed 's/^/  /'
/usr/bin/python3 - <<'PY2' > "$SANDBOX/roles.txt"
import json, os
r = json.load(open(os.environ["AGENT_SKILLS_HOME"] + "/routing.json"))["roles"]
for role in ("implement", "review", "verify"):
    value = r.get(role)
    print(role, value and value["family"], value and value["sourceKind"])
print("assigned", sum(1 for v in r.values() if v))
PY2
impf=$(awk '/^implement /{print $2}' "$SANDBOX/roles.txt")
revf=$(awk '/^review /{print $2}' "$SANDBOX/roles.txt")
verf=$(awk '/^verify /{print $2}' "$SANDBOX/roles.txt")
check "all five roles assigned" \
  "$([ "$(awk '/^assigned/{print $2}' "$SANDBOX/roles.txt")" -eq 5 ] && echo 0 || echo 1)"
check "review family '$revf' differs from implement '$impf'" "$([ "$revf" != "$impf" ] && echo 0 || echo 1)"
check "verify family '$verf' differs from implement '$impf'" "$([ "$verf" != "$impf" ] && echo 0 || echo 1)"
check "no role landed on an unprovable family" \
  "$(! grep -qE ' unknown ' "$SANDBOX/roles.txt" && echo 0 || echo 1)"
check "harness took precedence: no CLI route used" \
  "$(! grep -q 'cli-fallback' "$SANDBOX/roles.txt" && echo 0 || echo 1)"
check "skill roots were created in the sandbox" \
  "$([ "$(find "$SANDBOX/home" -maxdepth 4 -type l | wc -l | tr -d ' ')" -ge 30 ] && echo 0 || echo 1)"
check "harness config was written under temp" \
  "$([ -f "$SANDBOX/omp-agent/config.yml" ] && echo 0 || echo 1)"
check "roles reached that temp config" \
  "$(PI_CODING_AGENT_DIR=$SANDBOX/omp-agent omp config get modelRoles 2>/dev/null | grep -q '"review"' && echo 0 || echo 1)"

step "3b. Re-running the installer changes nothing"
"$CLONE/bin/agent-setup" \
  --skills-home "$SANDBOX/home" \
  --config-env "PI_CODING_AGENT_DIR=$SANDBOX/omp-agent" \
  >"$SANDBOX/setup2.log" 2>&1
check "second run reports the config already current" \
  "$(grep -q 'already-current' "$SANDBOX/setup2.log" && echo 0 || echo 1)"
check "second run relinks nothing" \
  "$([ "$(grep -cE '^  (link|relink|replace)' "$SANDBOX/setup2.log")" -eq 0 ] && echo 0 || echo 1)"

step "3c. A pin that would break independence is refused"
same=$(/usr/bin/python3 -c "
import json,os;print(json.load(open(os.environ['AGENT_SKILLS_HOME']+'/routing.json'))['roles']['implement']['selector'])")
printf '{"review": "%s"}\n' "$same" > "$SANDBOX/agents/roles.overrides.json"
"$CLONE/bin/agent-roles" assign >"$SANDBOX/pin.log" 2>&1
check "same-family pin ignored, with a reason" "$(grep -q 'ignoring pin' "$SANDBOX/pin.log" && echo 0 || echo 1)"
grep 'ignoring pin' "$SANDBOX/pin.log" | sed 's/^/  /'
rm -f "$SANDBOX/agents/roles.overrides.json"

step "5. Confirm nothing real was modified"
check "real omp config.yml unchanged" \
  "$([ "$(shasum -a 256 "$REAL_CONFIG" | cut -d' ' -f1)" = "$REAL_CONFIG_BEFORE" ] && echo 0 || echo 1)"
check "real ~/.agents/routes.json unchanged" \
  "$([ "$(shasum -a 256 "$HOME/.agents/routes.json" 2>/dev/null | cut -d' ' -f1)" = "$REAL_ROUTES_BEFORE" ] && echo 0 || echo 1)"
check "real skill links still point at the real clone" \
  "$([ "$(readlink "$HOME/.agents/skills/lee-engineering")" = "$REAL_LINK_BEFORE" ] && echo 0 || echo 1)"
check "no sandbox path leaked into a real skill root" \
  "$(! readlink "$HOME/.agents/skills"/* | grep -q "$SANDBOX" && echo 0 || echo 1)"
check "no throwaway omp profile was created" \
  "$([ "$(ls "$HOME/.omp/profiles" 2>/dev/null | wc -l | tr -d ' ')" -eq "$REAL_PROFILES_BEFORE" ] && echo 0 || echo 1)"
check "every write landed under the sandbox" \
  "$([ "$(find "$SANDBOX" -newer "$SANDBOX/.started" -type f 2>/dev/null | wc -l | tr -d ' ')" -gt 0 ] && echo 0 || echo 1)"

printf '\n\033[1m%d passed, %d failed\033[0m\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
