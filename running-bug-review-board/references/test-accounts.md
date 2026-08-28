# Test account playbook

A QA pass without test accounts is a QA pass that won't run. Most apps
ship with provider-specific dev/test modes that issue free credentials
without sending real emails or charging cards. This reference catalogs
common providers; if yours isn't listed, **ask the user**.

## Contents

- The "ask the user" pattern
- Email suffix pattern (universal)
- Provider playbook
- Payment provider test credentials
- SMS / Phone test fixtures
- Storing credentials
- Persona -> permission mapping
- Fresh-user vs returning-user accounts
- After provisioning
- Shared test artifacts

## The "ask the user" pattern

If the repo doesn't document a test account playbook, ask **before
guessing**. Sample question:

> I need test accounts for the QA pass. Could you point me at:
>
> 1. Auth provider docs / dev mode for test users
> 2. An admin account I can use, OR permission to create one
> 3. The convention for test email suffixes per run (e.g. `+run0526`)
> 4. Any payment / 3rd-party provider test credentials needed for the
>    flows I'll test (Stripe test mode, Twilio test phones, etc.)
>
> If none exists, I can document one as part of the pass.

## Email suffix pattern (universal)

Even when an auth provider doesn't have explicit test mode, use:

```
<persona>+<tag>+run<MMDD>[-<shard>]@example.com
```

Examples:
- `qa-admin+test+run0526@example.com`
- `qa-member+test+run0526-shardC@example.com`

The `+run<MMDD>` suffix avoids collisions with prior pass accounts. The
shard suffix avoids collisions between parallel agents in the same pass.
`example.com` is reserved by IANA — never sends real email.

## Provider playbook

### Clerk (the pattern in Mokuhoe)

Clerk dev instances accept test fixtures with no real email/SMS:

| Field | Value |
|-------|-------|
| Email | any `*+clerk_test+<tag>@example.com` |
| Password | any strong password |
| OTP | **`424242`** (always) |
| Phone | `+1 (XXX) 555-0100`–`555-0199` |

Reference: https://clerk.com/docs/guides/development/testing/test-emails-and-phones

Sign-up flow: email + password → Continue → enter `424242` on verify
screen (Clerk usually auto-advances). Sign-in: email + password →
Continue. If prompted for OTP `424242`.

### Auth0

Use the Auth0 Dashboard "Test User" or seed via Management API. Common
patterns:
- A Database connection with `Disable Sign Ups` off for the test env
- Magic Link: any address ending in `@example.com` resolves to a no-send
- M2M client for programmatic seeding

Ask the user if a seed script (`scripts/seed-test-users.ts`) exists.

### Supabase

Two options:
- **`seed.sql`** with INSERT INTO `auth.users` for known UUIDs and
  emails — usually committed in `supabase/seed.sql`
- **Local dev** with `supabase start` — auto-confirms emails so any
  signup works

For OTP-style email-only flows, the local Supabase dev mailbox renders at
`http://localhost:54324` (Inbucket). Pull OTP from there.

### Firebase Auth

Use the Auth Emulator (`firebase emulators:start --only auth`). Email
verification, OTP, and password reset are all rendered in the emulator
UI at `http://localhost:9099`. Never hits real users.

### Custom / homegrown auth

Look for:
- A seed script in `scripts/` or `db/seeds/`
- Fixtures in `__fixtures__/`, `test-data/`, `tests/factories/`
- A `dev:reset` or `db:fixtures` make/npm task

If none, ask the user. Do not start writing scenarios that require auth
without confirmed credentials.

### Magic.link / WorkOS / Stytch / SuperTokens

Each has a dev/test mode with documented test fixtures. Reference the
provider's docs (use Ref MCP or web search) before guessing OTPs.

## Payment provider test credentials

Common for any flow that touches checkout:

| Provider | Test card | Notes |
|----------|-----------|-------|
| Stripe | `4242 4242 4242 4242`, any future date, any CVC | https://docs.stripe.com/testing |
| Stripe (3DS) | `4000 0027 6000 3184` | Triggers SCA challenge |
| Stripe (decline) | `4000 0000 0000 0002` | Triggers card decline |
| PayPal sandbox | sandbox.paypal.com login | Separate sandbox account |
| Adyen | `5555 4444 3333 1111` etc. | https://docs.adyen.com/development-resources/testing/test-card-numbers/ |

For subscription cancellation / refund flows, ask the user if a Stripe
test event simulator (`stripe trigger`) is set up.

## SMS / Phone test fixtures

| Provider | Test number / OTP |
|----------|-------------------|
| Clerk | `+1 (XXX) 555-0100`–`555-0199` / OTP `424242` |
| Twilio | "Magic" numbers per the docs; `+15005550006` always succeeds |
| Vonage | Sandbox dashboard issues test sender + receiver |

## Storing credentials

**Never commit passwords or OAuth tokens to the repo.** Options:

- Team password manager (1Password, Bitwarden, Doppler)
- Encrypted `.env.test` not committed (use `.env.test.example` in repo)
- Per-run handoff in the coordinator merge doc (text — not in git)

The coordinator merge doc records the **email pattern** + **role**, never
the password. Pass passwords via the existing chat / DM thread or vault.

## Persona -> permission mapping

After picking accounts, write down what each can and cannot do. Saves
time later when running negative tests:

```
Admin
  ✓ Create / delete groups
  ✓ Invite, change roles, remove members
  ✓ Edit settings
  ✓ Cancel sessions

Co-admin
  ✓ Edit roster, sessions
  ✗ Delete group, remove admins, change billing

Member
  ✓ View, mark availability, chat
  ✗ Settings, invite, role changes

Non-member (any other authenticated user)
  ✗ /groups/[id] should 404 / show "not in group"
```

## Fresh-user vs returning-user accounts

A **fresh user** test starts from a brand-new account every time. Always
generate a new email — `<persona>+test+run<MMDD>-<scenario>@example.com`
— do not reuse a previously-onboarded one.

A **returning user** test reuses an account from earlier in the same
pass. Document who's been onboarded in the coordinator merge so other
agents can reuse the persona.

## After provisioning

In the coordinator merge / handoff doc, record:

```
## Shared test artifacts

| Key | Value |
|-----|-------|
| Group / org / workspace ID | <id> |
| Primary invite URL | http://localhost:3000/sign-up?invite=<code> |
| Admin email | admin+test+run0526@example.com |
| Admin password | (vault) |
| OTP fixture | 424242 |
| Sign-up flow | email → password → Continue → OTP → /profile/setup |
| Sign-in flow | email → password → /dashboard |
```

Subsequent agents read this and don't redo provisioning.
