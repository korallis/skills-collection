import assert from "node:assert/strict";
import test from "node:test";

import {
  childEnvironment,
  safeHttpErrorDetail,
  safeStructuredDetail,
  shellCommand,
  validateBootstrapEndpoint,
} from "../scripts/sync_grok_t3_connect.mjs";

test("redacts nested T3 credentials from JSON failures", () => {
  const detail = safeHttpErrorDetail(
    JSON.stringify({
      error: "invalid_request",
      access_token: "relay-secret",
      accessToken: "relay-secret-camel",
      nested: {
        credential: "bootstrap-secret",
        subjectToken: "subject-secret",
        ticket: "websocket-secret",
      },
    }),
  );

  assert.equal(
    detail,
    '{"error":"invalid_request","access_token":"[REDACTED]","accessToken":"[REDACTED]","nested":{"credential":"[REDACTED]","subjectToken":"[REDACTED]","ticket":"[REDACTED]"}}',
  );
});

test("does not echo non-JSON HTTP failures", () => {
  const detail = safeHttpErrorDetail("Bearer secret-token\nupstream failed");

  assert.equal(detail, "non-JSON response body (35 bytes)");
  assert.doesNotMatch(detail, /secret-token/);
});

test("apply captures stderr and pins the exact release commit", () => {
  const releaseCommit = "a".repeat(40);
  const command = shellCommand("apply", releaseCommit);

  assert.match(command, /\} 2>&1\n\)/);
  assert.match(command, new RegExp(`rev-parse HEAD\\)\" != \"${releaseCommit}\"`));
  assert.ok(command.endsWith("\n"));
});

test("apply rejects an unpinned release", () => {
  assert.throws(() => shellCommand("apply"), /exact release commit/);
});

test("accepts only TLS-protected T3 bootstrap endpoints", () => {
  assert.doesNotThrow(() =>
    validateBootstrapEndpoint({
      endpoint: {
        httpBaseUrl: "https://environment.example",
        wsBaseUrl: "wss://environment.example/ws",
      },
    }),
  );
  assert.throws(
    () =>
      validateBootstrapEndpoint({
        endpoint: {
          httpBaseUrl: "http://environment.example",
          wsBaseUrl: "wss://environment.example/ws",
        },
      }),
    /HTTP endpoint must use https:/,
  );
  assert.throws(
    () =>
      validateBootstrapEndpoint({
        endpoint: {
          httpBaseUrl: "https://environment.example",
          wsBaseUrl: "ws://environment.example/ws",
        },
      }),
    /websocket endpoint must use wss:/,
  );
});

test("removes the T3 session token from child process environments", () => {
  const previous = process.env.T3_CONNECT_SESSION_TOKEN;
  process.env.T3_CONNECT_SESSION_TOKEN = "session-secret";
  try {
    assert.equal(childEnvironment().T3_CONNECT_SESSION_TOKEN, undefined);
  } finally {
    if (previous === undefined) delete process.env.T3_CONNECT_SESSION_TOKEN;
    else process.env.T3_CONNECT_SESSION_TOKEN = previous;
  }
});

test("redacts credentials from structured RPC failures", () => {
  const detail = safeStructuredDetail({
    _tag: "Defect",
    payload: { refreshToken: "refresh-secret", dpop: "proof-secret" },
  });

  assert.equal(
    detail,
    '{"_tag":"Defect","payload":{"refreshToken":"[REDACTED]","dpop":"[REDACTED]"}}',
  );
});
