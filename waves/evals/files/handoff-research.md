# Worker handoff -- research stream: login-timeout root cause

## Status
success

## Scope
External research: possible root causes for the login-timeout complaints
(auth vendor incidents, browser changes, known SSO issues). No ticket rows.

## Coverage
- Assigned: vendor status pages and community forums for May-June 2026
- Read: vendor changelog, vendor status page, two community forums
- Skipped: internal auth service logs (no access from this worker)

## Key findings
- [med] The auth vendor shipped a token-refresh change in early May 2026 that
  several customers publicly linked to longer login latencies -- evidence:
  vendor changelog entry 2026-05-02 and two independent forum threads --
  sources agreeing: 3
- [low] The timeout spike may correlate with the vendor's US-East degradation
  window in mid-May -- evidence: one community forum post; I could NOT find a
  matching incident on the vendor status page -- sources agreeing: 1

## Sources
- Vendor changelog (2026-05-02 entry); community forum threads (2)

## Confidence & verification
- Verified: the token-refresh change and its timing (cross-checked 3 sources).
- Single-sourced: the US-East degradation correlation -- one forum post, not
  confirmed by the vendor status page.
- Inferred: none.
- Unresolved / could not verify: no status-page entry found for the claimed
  degradation.
- Would change my conclusion: a vendor status-page incident record for
  mid-May US-East.

## Open questions / gaps
- Whether the affected tickets cluster in regions consistent with US-East.

## Suggested follow-ups
- Cross-reference ticket dates/regions against the vendor changelog window.
