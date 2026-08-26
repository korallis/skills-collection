# Capacity-aware route scheduling

Use this reference before each provider-backed dispatch wave. It defines the capacity evidence and
scheduling procedure for locally launched engineering harnesses.

## Record capacity by provider meter

A route identifies a harness and a model. A capacity pool identifies the meter that can stop that
route. Group routes that share a subscription, balance, rolling window, billing gate, or resource
lease. Count the pool once even when a catalog lists many models or several wrappers reach it.

Record this structure in the task ledger:

```text
CapacitySnapshot
  observedAt: RFC 3339 timestamp
  pools: CapacityPoolSnapshot[]

CapacityPoolSnapshot
  poolId: stable provider meter or local resource ID
  routeIds: every candidate route drawing from this pool
  availability: unknown | available | constrained | exhausted | blocked
  windows: CapacityWindowSnapshot[]
  overflowCredit: available | unavailable | unlimited | unknown
  evidence: account view, CLI result, or local resource proof

CapacityWindowSnapshot
  windowId: provider label or duration
  usedPercent: 0 through 100, or unknown
  resetsAt: RFC 3339 timestamp or unknown
  durationMinutes: positive integer or unknown
```

Keep account identifiers, credentials, tokens, and invoice details out of the ledger. Record only the
capacity facts needed to schedule work.

Use the availability states consistently:

- `unknown`: current request capacity has not been proved.
- `available`: the route can accept normal packets.
- `constrained`: provider warnings or an explicit review reserve limit the route to required or small
  packets.
- `exhausted`: an applicable limit blocks requests.
- `blocked`: authentication, billing, policy, or account state blocks requests.

An account can expose more than one applicable window. A route is exhausted when an applicable
required window is exhausted and no permitted overflow credit remains, or when the provider returns a
definitive exhaustion response. An empty optional credit balance does not exhaust unused included
allowance. For a named subpool, record both the shared window and the named window. For example, a
Claude model can draw from both the all-model weekly pool and a model-specific weekly pool.

## Collect account-native evidence

Use a provider's account view or local usage command before a model prompt. A successful model-list
or authentication command proves identity, not request capacity. Use a tool-free canary only when the
account surface cannot prove request availability or after an account repair.

### Codex

Call `account/rateLimits/read` through `codex app-server`. Record every entry in
`rateLimitsByLimitId`, including each primary and secondary window, credit state, and reset credit
count. Treat each `limitId` as a separate capacity pool unless the response proves that two IDs share
one meter. `resetsAt` is a Unix timestamp in seconds. Convert it to an RFC 3339 timestamp with an
explicit offset before recording the snapshot.

### Claude Code

Run the local usage command without inference or tools:

```bash
claude -p "/usage" \
  --output-format json \
  --permission-mode plan \
  --tools "" \
  --no-session-persistence \
  --safe-mode
```

Record the all-model window and every named model window from the result. An API `429` overrides an
older usage snapshot and marks the applicable pool exhausted until its reported reset. Read the JSON
`result`; a zero process exit does not prove capacity.

### Grok Build

Start the interactive CLI through `lee-grok`, then open `/usage`. Record the weekly percentage,
local reset time, prepaid balance, and auto-top-up state that the panel exposes. The direct wrappers
`lee-grok` and `lee-grok-review` share the same provider pool unless the account view proves
otherwise.

If no interactive terminal is available, use one fixed, tool-free, one-turn canary. A `402` with
`usage balance exhausted` marks the pool exhausted. The canary does not establish remaining
percentage when it succeeds, so retain `usedPercent: unknown`.

### Cursor Agent

Run `cursor-agent status` to confirm the account and tier. Read the account usage or billing view for
remaining usage and reset times. Cursor catalog models share the account billing gate unless the
account view exposes separate meters. `lee-cursor-grok` therefore uses Cursor capacity, not the
direct Grok Build pool.

After an invoice payment, authentication change, or ambiguous account state, run one bounded
read-only canary in an empty trusted directory. A successful canary marks request capacity available.
An unpaid-invoice response marks the entire Cursor account pool blocked.

### Self-hosted routes

Use the current service health, GPU or accelerator lease, queue depth, and task admission as capacity
evidence. A self-hosted route has no provider reset time. It remains unavailable when the named task
has not passed its evaluation or when its resource lease is unavailable. Schedule an admitted
self-hosted route from its current queue and resource headroom. Do not apply the percentage and reset
formula used for provider windows.

## Allocate a dispatch wave

Apply this order:

1. Remove routes that fail authority, data, local-execution, task-fit, model-family, or writer-lease
   gates.
2. Group the remaining routes by capacity pool. Remove exhausted and blocked pools from normal
   dispatch. Limit an unknown-meter pool to one packet and a constrained pool to required work.
3. Protect the last available non-author family when the task has an independent-review gate. If a
   comparable receipt exists, reserve one review-sized packet. Otherwise mark the pool constrained
   and keep it out of discretionary work.
4. Estimate each packet as small, medium, or large from receipts for the same task shape. Keep the
   estimate unknown when no comparable receipt exists.
5. For each known window, calculate ordinary headroom from the provider's remaining percentage after
   any explicit review reserve. Divide that headroom by the hours until reset. The smallest result
   across a route's applicable windows is its binding sustainable allowance. Treat a window with an
   unknown percentage or reset time as unknown capacity.
6. Assign the next packet to the suitable pool with the largest binding sustainable allowance. Use
   the best task-fit route inside that pool. Rotate equal choices and avoid consecutive discretionary
   packets on one pool while another suitable pool has comparable allowance.
7. For a pool with unknown usage, assign at most one packet in the wave. Choose the smallest suitable
   packet. Use its receipt and a refreshed account view before assigning more.
8. Update the ledger after every receipt. Refresh all pools before the next wave.

The calculation paces each pool against its own reset. It does not claim that one percentage point or
one message costs the same across providers. Use measured receipts to correct packet-size estimates.
An explicit user route choice wins the capacity preference when the route remains admitted and
available.

## Invalidate stale evidence

Invalidate a pool snapshot immediately when any of these events occurs:

- the provider returns a quota, billing, authentication, or capacity error;
- the recorded reset time passes;
- the account, subscription, credit balance, model catalog, or harness changes;
- a long-running packet crosses the reset time; or
- a dispatch wave completes.

After invalidation, set the pool to `unknown`. Re-read the account surface or run the bounded canary
before dispatch. A clock transition alone never changes a pool from exhausted or blocked to
available.

If no admitted pool can accept the packet, record each unavailable or denied pool and stop. Waiting
for a known reset is valid when the task permits it. A capacity failure never authorizes a new data
route, cloud coding agent, extra spend, subscription change, or review waiver.
