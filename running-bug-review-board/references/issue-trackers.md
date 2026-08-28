# Issue tracker integration — discover, confirm, sync

QA bugs live in markdown (`docs/qa/bug-reports/BUG-*.md`) by default.
Engineering usually lives in an issue tracker — Linear, GitHub Issues,
Jira, or Notion. This reference describes how the skill brings the two
together **only after the user confirms which tracker they want**.

The skill never assumes a tracker silently. Even when signals are
obvious, the agent surfaces what it found and asks before writing
`docs/qa/qa-config.json`.

## Contents

- Why sync at all
- Discovery ceremony (do this once per repo)
- Adapter — Linear (first-class)
- Adapter — GitHub Issues (first-class)
- Adapter — Jira (templated)
- Adapter — Notion (templated)
- When to sync
- Bi-directional sync
- Sync surface in run + merge docs
- Anti-patterns
- Extending — adding a new tracker

## Why sync at all

Markdown alone is honest but isolated. Engineering's PRs, standups, and
dashboards live in the tracker. Without a sync, QA findings and
engineering's progress drift apart. With a sync:

- A bug filed in QA appears in the tracker with steps, evidence link,
  priority, and the Test ID — engineering can act without re-reading.
- A status flip in the tracker (`fixed`, `verified`) flows back into
  the markdown automatically, so the next QA pass doesn't ask about
  something already resolved.
- The interactive BRB ([brb-interactive.md](brb-interactive.md)) becomes
  a real bridge between the two worlds, not a duplicated to-do list.

## Discovery ceremony (do this once per repo)

When the agent first encounters a repo without `docs/qa/qa-config.json`
(or with `issueTracker.type` unset), it runs this ceremony **before
filing any bugs**.

### Step 1 — Scan for signals

Probe in this order; record what's present and what's absent. Don't act
on findings yet.

| Signal | Suggests |
|--------|----------|
| `~/.linear/` directory | Linear used historically on this Mac |
| `LINEAR_API_KEY` env var | Linear API access available |
| Linear MCP server registered (e.g. `mcp list` returns `linear`) | Linear MCP already wired up — strong signal |
| `.github/` directory + `gh auth status` clean | GitHub Issues is a viable target |
| Existing GitHub issues with label `qa` or `bug` | GitHub already used for QA |
| `JIRA_API_TOKEN` env var | Jira API access available |
| URL like `*.atlassian.net` in README, CONTRIBUTING, or git remotes | Jira likely in use |
| `acli` / `jira-cli` on `PATH` | Jira CLI installed |
| `notion.so/` or `notion.site/` URLs in README | Notion documentation |
| Notion MCP registered | Notion MCP available |
| Mentions in `CONTRIBUTING.md` ("file bugs in <X>", "report via <Y>") | Strongest signal — repo's own docs say where bugs go |

### Step 2 — Present findings to the user

Surface every signal that was found, plus every common tracker that was
checked but absent. Do not push a recommendation. Example:

```
I'm preparing to file QA bugs. Here's what I detected in this repo:

Signals present
  • LINEAR_API_KEY is set in your shell.
  • Linear MCP server is registered.
  • This repo is on GitHub and `gh auth status` is clean.

Signals absent
  • No Atlassian URL in README; no `.jira/`; no JIRA_API_TOKEN.
  • No Notion workspace mentioned in README.
  • CONTRIBUTING.md does not name a preferred tracker.

Where would you like QA bugs to land?

  1. Linear (Linear MCP is already wired up — likely the cleanest path)
  2. GitHub Issues (I'd use `gh issue create`)
  3. Jira (you'd give me the project key + token reference)
  4. Notion (you'd give me the database ID + Notion MCP)
  5. Just markdown in `docs/qa/bug-reports/` — no sync
  6. A mix (different trackers for different phases)

Tell me which one and I'll write it into `docs/qa/qa-config.json`.
```

### Step 3 — Wait for the user

Don't push back, don't infer, don't write the config. Wait.

If the user says "just markdown" or "no tracker", record that explicitly
so the ceremony doesn't repeat.

### Step 4 — Write `docs/qa/qa-config.json`

Once confirmed, scaffold the config from
[templates/qa-config.example.json](templates/qa-config.example.json) and
fill in the chosen tracker. Always include provenance:

```jsonc
{
  "version": 1,
  "discoveredAt": "2026-05-27T18:23:00Z",
  "confirmedBy": "user",
  "issueTracker": {
    "type": "linear",
    "syncOnFile": false,
    "pull": {
      "onBRBStart": true,
      "onReTest": true,
      "window": "since-last-sync",
      "createLocalForUntracked": "ask"
    },
    "linear": { … }
  },
  …
}
```

### Step 5 — Bootstrap per-tracker details

After the user picks a tracker, gather the minimum needed:

- **Linear**: enumerate the user's teams via Linear MCP
  (`linear_search_issues` with a wildcard scope, or whatever lookup the
  installed MCP exposes), then list them. Ask the user to pick. Write
  the chosen `teamId` into the config. If MCP enumeration isn't wired
  up, fall back to asking the user to paste the team ID.
- **GitHub**: confirm `gh auth status`; ask whether to target the
  current repo or a different one. Run a label bootstrap (see below).
- **Jira**: ask for `baseUrl` (e.g. `https://acme.atlassian.net`) and
  `projectKey` (e.g. `QA`). Token reference goes in the user's secret
  store, not the config.
- **Notion**: ask for the database ID and confirm a Notion MCP is
  registered.

## Adapter — Linear (first-class)

Linear's official MCP server is the cleanest path. Install once per
client; the OAuth flow handles auth.

### Install

```bash
# Claude Code
claude mcp add --transport http linear-server https://mcp.linear.app/mcp

# Codex CLI
codex mcp add linear --url https://mcp.linear.app/mcp

# Any client without remote-MCP support
npx -y mcp-remote https://mcp.linear.app/mcp
```

Server URL: `https://mcp.linear.app/mcp` (Streamable HTTP) or
`https://mcp.linear.app/sse`. Both use OAuth 2.1 with dynamic client
registration. Reference: <https://linear.app/docs/mcp>.

### Tools

| Tool | Use |
|------|-----|
| `linear_create_issue` | Create a bug. Required: `title`, `team_id`. Optional: `description` (markdown), `priority` (0–4), `labels`, `assignee_id`, `project_id` |
| `linear_update_issue` | Update title / description / status / priority / labels |
| `linear_add_comment` | Append a comment to an issue |
| `linear_search_issues` | Search by team / label / state / updated-since — used by **pull** |
| `linear_get_user_issues` | Issues assigned to a user |

(Tool names vary slightly across MCP server implementations; check
`mcp list` in your client.)

### Priority and label map

```jsonc
"linear": {
  "teamId": "ABC-12345",
  "labelMap": { "P0": "urgent", "P1": "high", "P2": "low" },
  "extraLabels": ["qa", "brb"],
  "mcpServer": "linear"
}
```

Linear's numeric priority: 1=urgent, 2=high, 3=medium, 4=low. Map BRB's
P0 → 1, P1 → 2, P2 → 4.

### Dedupe key

Bug front-matter row `Tracker / Linear`. Stores the Linear issue
identifier (e.g. `LIN-1234` or `ENG-512`). Presence means "already
synced"; absence means "needs create".

### Rate limits

1,500 requests/hour per API key. Pulling in batches is fine; the
helper script ([../scripts/bugs-needing-pull.sh](../scripts/bugs-needing-pull.sh))
chunks the work so the agent stays well under the limit.

## Adapter — GitHub Issues (first-class)

`gh` is already authenticated in most environments.

### Create

```bash
gh issue create \
  --title "BUG-007 — Stale invite in storage joins user to wrong group" \
  --body-file docs/qa/bug-reports/BUG-007-stale-invite.md \
  --label bug,P0,phase:2 \
  --assignee @me
```

### Update status

```bash
gh issue edit 87 --add-label fixed --remove-label open
gh issue edit 87 --add-label verified --remove-label fixed
```

### Read for pull

```bash
gh issue list \
  --label qa \
  --state all \
  --json number,title,state,labels,assignees,updatedAt,comments,closedAt,body \
  --search "label:qa updated:>=2026-05-26"
```

### Label bootstrap (run once)

```bash
gh label create P0 --color d73a4a --description "QA: blocks core flow"
gh label create P1 --color e99695 --description "QA: feature broken, workaround exists"
gh label create P2 --color fbca04 --description "QA: cosmetic / nit"
gh label create qa --color 0e8a16 --description "Filed by QA"
gh label create brb --color 5319e7 --description "Triaged in Bug Review Board"
gh label create phase:1 --color cccccc
gh label create phase:2 --color cccccc
# … per phase as needed
```

### Dedupe key

Bug front-matter row `Tracker / GitHub`. Stores `#NN` (e.g. `#87`) or
the full URL if cross-repo.

## Adapter — Jira (templated)

Use `acli` / `jira-cli` if the user has them installed, otherwise REST.

### Create (REST)

```bash
curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  -H 'Content-Type: application/json' \
  "$JIRA_BASE_URL/rest/api/3/issue" \
  -d @- <<EOF
{
  "fields": {
    "project":   { "key": "$JIRA_PROJECT_KEY" },
    "summary":   "BUG-007 — Stale invite in storage joins user to wrong group",
    "issuetype": { "name": "Bug" },
    "priority":  { "name": "Highest" },
    "labels":    ["qa", "brb", "phase-2"]
  }
}
EOF
```

### Create (`jira-cli`)

```bash
jira issue create \
  --project "$JIRA_PROJECT_KEY" \
  --type Bug \
  --summary "BUG-007 — …" \
  --priority Highest \
  --label qa --label brb --label phase-2 \
  --body-file docs/qa/bug-reports/BUG-007-stale-invite.md
```

### Priority map

```jsonc
"jira": {
  "baseUrl": "https://acme.atlassian.net",
  "projectKey": "QA",
  "labelMap": { "P0": "Highest", "P1": "High", "P2": "Low" }
}
```

### Dedupe key

Bug front-matter row `Tracker / Jira`. Stores e.g. `QA-1042`.

## Adapter — Notion (templated)

Use the Notion MCP server. Configure a database with these properties:

| Property | Type | Maps to |
|----------|------|---------|
| `Title` | Title | Bug title |
| `Status` | Select | open / in-progress / fixed / verified / deferred / wontfix / duplicate |
| `Priority` | Select | P0 / P1 / P2 |
| `Phase` | Number | Phase number |
| `Test ID` | Rich text | e.g. `P2-C1` |
| `BUG ID` | Rich text | `BUG-007` (dedupe key) |
| `Reported on` | Date | First reported |
| `Source` | URL | Link back to the markdown file (relative path) |

### Config

```jsonc
"notion": {
  "databaseId": "abcd1234567890efghijklmnop",
  "mcpServer": "notion"
}
```

### Dedupe key

Notion page property `BUG ID` (canonical), plus front-matter row
`Tracker / Notion` storing the Notion page URL.

## When to sync

Two switches in `qa-config.json`:

- **`issueTracker.syncOnFile`** (default `false`).
  When `true`, the auto QA pass syncs every newly-filed bug immediately.
  When `false` (default), the auto pass keeps everything local. Sync
  happens at BRB time after a human has triaged. This keeps tracker
  noise down and lets QA edit drafts before they go up.
- **`issueTracker.pull.onBRBStart`** (default `true`).
  The interactive BRB starts by pulling. See **Bi-directional sync**
  below.

## Bi-directional sync

The skill supports three operations:

| Operation | Direction | When |
|-----------|-----------|------|
| **Push** | markdown → tracker | At file time if `syncOnFile == true`; otherwise at BRB time |
| **Pull** | tracker → markdown | Start of every BRB (`pull.onBRBStart`); before re-testing a known bug (`pull.onReTest`); on user request |
| **Reconcile** | bi-directional | When both sides changed between syncs |

### What gets pulled

For each bug whose `Tracker / <type>` row is populated:

- **Status** (open / in-progress / fixed / verified / deferred / wontfix /
  duplicate)
- **Priority** (P0 / P1 / P2 — if engineering re-prioritized)
- **Comments** added since `Tracker / lastSyncedAt`
- **Linked PR / commit** (Linear and GitHub auto-link these)
- **Assignee** (used by the `same-owner` heuristic in
  [triage-heuristics.md](triage-heuristics.md))

### Reconciliation rules

| Field | Rule |
|-------|------|
| Status `fixed`, `verified` | **Tracker wins.** Engineering's call. Append a Triage log entry. |
| Status `open`, `in-progress` | **Markdown wins.** QA's call. Push to tracker if it drifted. |
| Status `deferred`, `wontfix`, `duplicate` | **Surface to user; never auto-change.** These reflect deliberate decisions on both sides. |
| Priority | **Surface diff to user; never auto-change.** Re-prioritization is a real conversation. |
| Comments added in tracker | **Append to bug's Triage log** as `Tracker comment by <author> on <date>: …`. |
| Linked PR / commit | **Write to bug front-matter `Fixed in:`** field. |
| Tracker-only bug (no local match) | **Behavior depends on `pull.createLocalForUntracked`** (default `"ask"`). Options: `"ask"`, `"ignore"`, `"create"`. Never `"create"` silently. |

### Per-bug sync state

Add this row to every bug's front-matter on first push:

```
| **Tracker / lastSyncedAt** | 2026-05-27T18:23:00Z |
```

Updated by both push and pull operations. Drives the
`bugs-needing-pull.sh` staleness check.

### Pull workflow (numbered)

1. Read `qa-config.json` for the active tracker and `pull.window`
   setting.
2. Compute the lookback: by default, the most recent `lastSyncedAt`
   across local bugs, minus 1 hour of slack. (`pull.window` can override
   to a fixed duration like `"24h"`.)
3. Query the tracker for bugs matching the QA label set
   (`qa`, `brb`, `phase:N`) updated since the lookback.
4. For each tracker bug:
   - Find local match via front-matter `Tracker / <type>` row.
   - If no match: add to "untracked-locally" list.
   - If match: diff fields; apply reconciliation rules; record changes
     in the bug's Triage log.
5. Update `Tracker / lastSyncedAt` on every touched bug.
6. Apply `pull.createLocalForUntracked` to the untracked list.
7. Print a summary:
   ```
   Pulled 12 bugs.
   Updated  4 (BUG-007 → fixed, BUG-012 → verified, …).
   Diverged 1 (BUG-019: tracker says P0, local says P1). Need user input.
   Untracked-locally 2 (LIN-3344, LIN-3347).
   ```

### Helper scripts

- [../scripts/bugs-needing-sync.sh](../scripts/bugs-needing-sync.sh) —
  lists bugs missing a tracker ID for the configured tracker. Use
  before push.
- [../scripts/bugs-needing-pull.sh](../scripts/bugs-needing-pull.sh) —
  lists bugs whose `Tracker / lastSyncedAt` is stale (default older
  than 24 h or missing). Use before pull.

Both helpers only enumerate. The agent runs the actual tracker calls
via MCP tools / CLI per the adapter sections above.

## Sync surface in run + merge docs

Every run report and coordinator merge that touches the tracker should
fill in the **Tracker sync** table:

| Tracker | Pushed (new) | Updated | Pulled | Diverged |
|---------|-------------:|--------:|-------:|---------:|
| linear  | 3            | 2       | 12     | 1        |

This shows up in both the markdown and the HTML report so the team can
see at a glance how the two sides are tracking.

## Anti-patterns

| Don't | Why |
|-------|-----|
| Pick a tracker silently because a signal was present | The user may have shifted away from that tracker; always ask |
| Auto-create local markdown for tracker-only bugs | Engineering may have filed a bug QA shouldn't claim; default is `"ask"` |
| Overwrite local QA notes when a Triage log entry duplicates a tracker comment | Use timestamp + author to dedupe |
| Pull silently | Every pull writes a summary the user sees |
| Sync `wontfix` bugs as fresh tracker issues | `wontfix` means "no further action"; don't reopen by mistake |
| Re-prioritize unilaterally from tracker → markdown or vice versa | Priority changes are a conversation; surface the diff |
| Paste secrets (API tokens, OAuth tokens) into the markdown bug or `qa-config.json` | Use the user's secret manager / environment variables |
| Double-file: file the same bug as `BUG-008` and `BUG-009` in two passes | Check the heuristics in [triage-heuristics.md](triage-heuristics.md) first |

## Extending — adding a new tracker

Copy a `## Adapter — <Tracker>` section above. Fill in: install, auth,
create-bug shape, status-flip shape, label map, dedupe key (a new
front-matter row), anti-patterns. Add the type string to
[templates/qa-config.example.json](templates/qa-config.example.json) and
list it in the discovery ceremony's user prompt. See
[extending-the-skill.md](extending-the-skill.md).
