#!/usr/bin/env node
/** Converge the Lee/Grok harness across every linked T3 Connect environment. */

import { execFileSync } from "node:child_process";
import {
  createHash,
  generateKeyPairSync,
  randomUUID,
  sign,
} from "node:crypto";
import { readFileSync, realpathSync, statSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join, resolve } from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const RELAY_URL = "https://relay.t3.codes";
const TOKEN_EXCHANGE_GRANT = "urn:ietf:params:oauth:grant-type:token-exchange";
const ACCESS_TOKEN_TYPE = "urn:ietf:params:oauth:token-type:access_token";
const RELAY_SUBJECT_TOKEN_TYPE = "urn:ietf:params:oauth:token-type:jwt";
const ENVIRONMENT_SUBJECT_TOKEN_TYPE =
  "urn:t3:params:oauth:token-type:environment-bootstrap";
const RESULT_MARKER = "__LEE_GROK_T3_RESULT__";
const DEFAULT_TIMEOUT_SECONDS = 240;
const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const sourceSkill = resolve(scriptDirectory, "..");

class FleetError extends Error {}

const SENSITIVE_RESPONSE_KEYS = new Set([
  "access_token",
  "authorization",
  "credential",
  "dpop",
  "id_token",
  "refresh_token",
  "subject_token",
  "ticket",
]);

function usage() {
  return `Usage: sync_grok_t3_connect.mjs <list|apply|verify> [options]

Options:
  --base-dir PATH       T3 data directory (default: T3CODE_HOME or ~/.t3)
  --environment VALUE  Limit by exact environment id or label; repeatable
  --session-token-file PATH
                        Read a short-lived T3 client t3-relay JWT from PATH
  --timeout SECONDS    Per-environment terminal timeout (default: ${DEFAULT_TIMEOUT_SECONDS})
  --json               Emit the final report as JSON (default for automation)`;
}

function parseArguments(argv) {
  const command = argv.shift();
  if (!new Set(["list", "apply", "verify"]).has(command)) {
    throw new FleetError(usage());
  }
  const options = {
    command,
    baseDir: process.env.T3CODE_HOME || join(homedir(), ".t3"),
    environments: [],
    sessionTokenFile: undefined,
    timeoutSeconds: DEFAULT_TIMEOUT_SECONDS,
  };
  while (argv.length > 0) {
    const argument = argv.shift();
    if (argument === "--json") continue;
    if (argument === "--base-dir") {
      options.baseDir = requiredValue(argument, argv.shift());
      continue;
    }
    if (argument === "--environment") {
      options.environments.push(requiredValue(argument, argv.shift()));
      continue;
    }
    if (argument === "--session-token-file") {
      options.sessionTokenFile = requiredValue(argument, argv.shift());
      continue;
    }
    if (argument === "--timeout") {
      const value = Number(requiredValue(argument, argv.shift()));
      if (!Number.isInteger(value) || value < 10 || value > 1800) {
        throw new FleetError("--timeout must be an integer from 10 through 1800");
      }
      options.timeoutSeconds = value;
      continue;
    }
    throw new FleetError(`unknown argument: ${argument}\n\n${usage()}`);
  }
  return options;
}

function requiredValue(flag, value) {
  if (!value || value.startsWith("--")) {
    throw new FleetError(`${flag} requires a value`);
  }
  return value;
}

function base64Url(value) {
  return Buffer.from(value).toString("base64url");
}

function stablePublicJwk(jwk) {
  return { crv: jwk.crv, kty: jwk.kty, x: jwk.x, y: jwk.y };
}

function normalizeHtu(value) {
  const url = new URL(value);
  url.hash = "";
  url.search = "";
  return url.toString();
}

export function childEnvironment() {
  const environment = { ...process.env };
  delete environment.T3_CONNECT_SESSION_TOKEN;
  delete environment.T3_SERVICE_LAUNCHER_CONTEXT;
  return environment;
}

function requireProtocol(value, protocol, label) {
  const url = new URL(value);
  if (url.protocol !== protocol) {
    throw new FleetError(`${label} must use ${protocol}`);
  }
  return url;
}

export function validateBootstrapEndpoint(bootstrap) {
  if (!bootstrap?.endpoint) throw new FleetError("T3 bootstrap endpoint is absent");
  requireProtocol(bootstrap.endpoint.httpBaseUrl, "https:", "T3 HTTP endpoint");
  requireProtocol(bootstrap.endpoint.wsBaseUrl, "wss:", "T3 websocket endpoint");
}

function makeDpopSigner() {
  const { privateKey, publicKey } = generateKeyPairSync("ec", {
    namedCurve: "P-256",
  });
  const publicJwk = stablePublicJwk(publicKey.export({ format: "jwk" }));
  const thumbprint = base64Url(
    createHash("sha256")
      .update(JSON.stringify(publicJwk))
      .digest(),
  );

  return {
    thumbprint,
    proof({ method, url, accessToken }) {
      const header = { typ: "dpop+jwt", alg: "ES256", jwk: publicJwk };
      const payload = {
        htm: method.toUpperCase(),
        htu: normalizeHtu(url),
        jti: randomUUID(),
        iat: Math.floor(Date.now() / 1000),
      };
      if (accessToken) {
        payload.ath = base64Url(createHash("sha256").update(accessToken).digest());
      }
      const encodedHeader = base64Url(JSON.stringify(header));
      const encodedPayload = base64Url(JSON.stringify(payload));
      const signingInput = `${encodedHeader}.${encodedPayload}`;
      const signature = sign("sha256", Buffer.from(signingInput), {
        key: privateKey,
        dsaEncoding: "ieee-p1363",
      });
      return `${signingInput}.${base64Url(signature)}`;
    },
  };
}

function redactResponseValue(value, key = "") {
  const normalizedKey = key
    .replace(/([a-z0-9])([A-Z])/g, "$1_$2")
    .toLowerCase()
    .replaceAll("-", "_");
  if (SENSITIVE_RESPONSE_KEYS.has(normalizedKey)) return "[REDACTED]";
  if (Array.isArray(value)) return value.map((entry) => redactResponseValue(entry));
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([entryKey, entryValue]) => [
        entryKey,
        redactResponseValue(entryValue, entryKey),
      ]),
    );
  }
  return value;
}

export function safeStructuredDetail(value) {
  return JSON.stringify(redactResponseValue(value)).slice(0, 1000);
}

export function safeHttpErrorDetail(body) {
  try {
    return safeStructuredDetail(JSON.parse(body));
  } catch {
    return `non-JSON response body (${Buffer.byteLength(body, "utf8")} bytes)`;
  }
}

async function responseJson(response, operation) {
  const body = await response.text();
  if (!response.ok) {
    throw new FleetError(
      `${operation} failed with HTTP ${response.status}: ${safeHttpErrorDetail(body)}`,
    );
  }
  try {
    return JSON.parse(body);
  } catch (error) {
    throw new FleetError(`${operation} returned invalid JSON: ${error.message}`);
  }
}

async function listEnvironments(clerkToken) {
  const response = await fetch(`${RELAY_URL}/v1/environments`, {
    headers: { authorization: `Bearer ${clerkToken}` },
    redirect: "error",
  });
  const body = await responseJson(response, "T3 environment discovery");
  return body.environments;
}

async function exchangeRelayToken(clerkToken, signer) {
  const url = `${RELAY_URL}/v1/client/dpop-token`;
  const payload = new URLSearchParams({
    grant_type: TOKEN_EXCHANGE_GRANT,
    subject_token: clerkToken,
    subject_token_type: RELAY_SUBJECT_TOKEN_TYPE,
    requested_token_type: ACCESS_TOKEN_TYPE,
    resource: RELAY_URL,
    scope: "environment:connect",
    client_id: "t3-web",
  });
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "content-type": "application/x-www-form-urlencoded",
      dpop: signer.proof({ method: "POST", url }),
    },
    body: payload,
    redirect: "error",
  });
  return responseJson(response, "T3 relay token exchange");
}

async function obtainEnvironmentBootstrap(environment, relayToken, signer) {
  const url = `${RELAY_URL}/v1/environments/${encodeURIComponent(environment.environmentId)}/connect`;
  const response = await fetch(url, {
    method: "POST",
    headers: {
      authorization: `DPoP ${relayToken.access_token}`,
      "content-type": "application/json",
      dpop: signer.proof({
        method: "POST",
        url,
        accessToken: relayToken.access_token,
      }),
    },
    body: JSON.stringify({ clientProofKeyThumbprint: signer.thumbprint }),
    redirect: "error",
  });
  const body = await responseJson(response, `connect ${environment.label}`);
  if (body.environmentId !== environment.environmentId) {
    throw new FleetError(`relay returned the wrong environment for ${environment.label}`);
  }
  validateBootstrapEndpoint(body);
  return body;
}

async function exchangeEnvironmentToken(bootstrap, signer) {
  const url = new URL("/oauth/token", bootstrap.endpoint.httpBaseUrl).toString();
  const payload = new URLSearchParams({
    grant_type: TOKEN_EXCHANGE_GRANT,
    subject_token: bootstrap.credential,
    subject_token_type: ENVIRONMENT_SUBJECT_TOKEN_TYPE,
    requested_token_type: ACCESS_TOKEN_TYPE,
    scope: "terminal:operate",
    client_label: "Lee Grok harness fleet sync",
    client_device_type: "bot",
  });
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "content-type": "application/x-www-form-urlencoded",
      dpop: signer.proof({ method: "POST", url }),
    },
    body: payload,
    redirect: "error",
  });
  return responseJson(response, "T3 environment token exchange");
}

async function issueWebSocketTicket(bootstrap, environmentToken, signer) {
  const url = new URL(
    "/api/auth/websocket-ticket",
    bootstrap.endpoint.httpBaseUrl,
  ).toString();
  const response = await fetch(url, {
    method: "POST",
    headers: {
      authorization: `DPoP ${environmentToken.access_token}`,
      dpop: signer.proof({
        method: "POST",
        url,
        accessToken: environmentToken.access_token,
      }),
    },
    redirect: "error",
  });
  return responseJson(response, "T3 websocket authorization");
}

function websocketUrl(bootstrap, ticket) {
  const url = new URL(bootstrap.endpoint.wsBaseUrl);
  if (url.pathname === "" || url.pathname === "/") url.pathname = "/ws";
  url.searchParams.set("wsTicket", ticket.ticket);
  return url.toString();
}

class T3RpcClient {
  constructor(socket) {
    this.socket = socket;
    this.nextId = 1;
    this.pending = new Map();
    socket.addEventListener("message", (event) => this.receive(event.data));
    socket.addEventListener("close", () => {
      this.rejectPending(new FleetError("T3 websocket closed before the RPC completed"));
    });
  }

  rejectPending(error) {
    for (const pending of this.pending.values()) {
      clearTimeout(pending.timer);
      pending.reject(error);
    }
    this.pending.clear();
  }

  static async connect(url, timeoutMs) {
    const socket = new WebSocket(url);
    await new Promise((resolvePromise, rejectPromise) => {
      const timer = setTimeout(() => {
        socket.close();
        rejectPromise(new FleetError("timed out opening the T3 websocket"));
      }, timeoutMs);
      socket.addEventListener(
        "open",
        () => {
          clearTimeout(timer);
          resolvePromise();
        },
        { once: true },
      );
      socket.addEventListener(
        "error",
        () => {
          clearTimeout(timer);
          rejectPromise(new FleetError("could not open the T3 websocket"));
        },
        { once: true },
      );
    });
    return new T3RpcClient(socket);
  }

  receive(raw) {
    let decoded;
    try {
      decoded = JSON.parse(typeof raw === "string" ? raw : Buffer.from(raw).toString());
    } catch {
      return;
    }
    const messages = Array.isArray(decoded) ? decoded : [decoded];
    for (const message of messages) {
      if (message?._tag === "Ping") {
        this.socket.send(JSON.stringify({ _tag: "Pong" }));
        continue;
      }
      if (message?._tag === "Defect" || message?._tag === "ClientProtocolError") {
        this.rejectPending(
          new FleetError(`T3 RPC protocol error: ${safeStructuredDetail(message)}`),
        );
        continue;
      }
      if (message?._tag !== "Exit") continue;
      const pending = this.pending.get(String(message.requestId));
      if (!pending) continue;
      this.pending.delete(String(message.requestId));
      clearTimeout(pending.timer);
      if (message.exit?._tag === "Success") pending.resolve(message.exit.value);
      else pending.reject(new FleetError(`T3 RPC failed: ${safeStructuredDetail(message.exit)}`));
    }
  }

  request(tag, payload, timeoutMs = 30_000) {
    const id = String(this.nextId++);
    return new Promise((resolvePromise, rejectPromise) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        rejectPromise(new FleetError(`T3 RPC ${tag} timed out`));
      }, timeoutMs);
      this.pending.set(id, { resolve: resolvePromise, reject: rejectPromise, timer });
      this.socket.send(
        JSON.stringify({ _tag: "Request", id, tag, payload, headers: [] }),
      );
    });
  }

  close() {
    this.socket.close(1000, "fleet operation complete");
  }
}

export function shellCommand(command, releaseCommit) {
  if (command === "apply" && !/^[0-9a-f]{40,64}$/.test(releaseCommit || "")) {
    throw new FleetError("apply requires an exact release commit");
  }
  const checkoutSelection = `
if [ -d /data/matilda/tooling ]; then
  checkout=/data/matilda/tooling/skills-collection-source
elif [ "$(uname -s)" = Darwin ]; then
  checkout="$HOME/Library/Application Support/Lee Engineering/skills-collection"
else
  checkout="\${XDG_DATA_HOME:-$HOME/.local/share}/lee-skills-collection"
fi`;
  const updateCheckout = `
if [ -e "$checkout" ] && [ ! -d "$checkout/.git" ]; then
  echo "refusing non-git canonical checkout: $checkout" >&2
  exit 1
fi
if [ -d "$checkout/.git" ]; then
  if [ -n "$(git -C "$checkout" status --porcelain)" ]; then
    echo "refusing dirty canonical checkout: $checkout" >&2
    exit 1
  fi
  GIT_TERMINAL_PROMPT=0 git -C "$checkout" fetch --prune origin main
  git -C "$checkout" checkout main
  git -C "$checkout" merge --ff-only origin/main
else
  mkdir -p "$(dirname "$checkout")"
  GIT_TERMINAL_PROMPT=0 git clone --branch main --single-branch \
    https://github.com/korallis/skills-collection.git "$checkout"
fi`;
  const verifyRelease = `
if [ "$(git -C "$checkout" rev-parse HEAD)" != "${releaseCommit}" ]; then
  echo "remote main does not match release commit ${releaseCommit}" >&2
  exit 1
fi`;
  const operation =
    command === "apply"
      ? `${updateCheckout}
${verifyRelease}
python3 "$checkout/lee-engineering/scripts/sync_grok_harness.py" install --json >/dev/null
python3 "$checkout/lee-engineering/scripts/sync_grok_harness.py" verify --json`
      : `python3 "$HOME/.agents/skills/lee-engineering/scripts/sync_grok_harness.py" verify --json`;
  return `
set +e
lee_grok_output=$(
  {
    set -eu
    umask 077
    ${command === "apply" ? checkoutSelection : ""}
    ${operation}
  } 2>&1
)
lee_grok_status=$?
lee_grok_encoded=$(printf %s "$lee_grok_output" | base64 | tr -d '\\n')
printf '\\n${RESULT_MARKER}%s:%s\\n' "$lee_grok_status" "$lee_grok_encoded"
`.trimStart();
}

function parseTerminalResult(history) {
  const expression = new RegExp(`${RESULT_MARKER}(\\d+):([A-Za-z0-9+/=]*)`);
  const match = expression.exec(history);
  if (!match) return null;
  const output = Buffer.from(match[2], "base64").toString("utf8");
  if (Number(match[1]) !== 0) throw new FleetError(output || "remote command failed");
  const lines = output.split(/\r?\n/).filter(Boolean).reverse();
  for (const line of lines) {
    try {
      return JSON.parse(line);
    } catch {}
  }
  throw new FleetError(`remote verifier returned invalid JSON: ${output.slice(0, 1000)}`);
}

async function runInEnvironment(
  environment,
  operation,
  releaseCommit,
  relayToken,
  signer,
  timeoutMs,
) {
  const bootstrap = await obtainEnvironmentBootstrap(environment, relayToken, signer);
  const environmentToken = await exchangeEnvironmentToken(bootstrap, signer);
  const ticket = await issueWebSocketTicket(bootstrap, environmentToken, signer);
  const client = await T3RpcClient.connect(websocketUrl(bootstrap, ticket), 15_000);
  const threadId = `lee-grok-fleet-${randomUUID()}`;
  const terminalId = "term-1";
  try {
    await client.request("terminal.open", {
      threadId,
      terminalId,
      cwd: "/",
      cols: 120,
      rows: 40,
    });
    await client.request("terminal.write", {
      threadId,
      terminalId,
      data: shellCommand(operation, releaseCommit),
    });
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      await new Promise((resolvePromise) => setTimeout(resolvePromise, 1000));
      const snapshot = await client.request("terminal.open", {
        threadId,
        terminalId,
        cwd: "/",
        cols: 120,
        rows: 40,
      });
      const report = parseTerminalResult(snapshot.history);
      if (report) return report;
    }
    throw new FleetError(`${operation} timed out after ${timeoutMs / 1000} seconds`);
  } finally {
    await client
      .request("terminal.close", { threadId, terminalId, deleteHistory: true }, 10_000)
      .catch(() => {});
    client.close();
  }
}

function refreshAndReadClerkToken(baseDir) {
  try {
    execFileSync(
      "t3",
      ["connect", "login", "--base-dir", resolve(baseDir)],
      { env: childEnvironment(), stdio: "pipe" },
    );
  } catch (error) {
    throw new FleetError(`could not refresh T3 Connect authorization: ${error.message}`);
  }
  const tokenPath = join(resolve(baseDir), "userdata", "secrets", "cloud-cli-oauth-token.bin");
  try {
    assertPrivateFile(tokenPath, "local T3 Connect authorization");
    const token = JSON.parse(readFileSync(tokenPath, "utf8"));
    if (!token.accessToken) throw new Error("accessToken is absent");
    return token.accessToken;
  } catch (error) {
    throw new FleetError(`could not read the local T3 Connect authorization: ${error.message}`);
  }
}

function assertPrivateFile(path, label) {
  if (process.platform !== "win32" && (statSync(path).mode & 0o077) !== 0) {
    throw new Error(`${label} must not be accessible by group or other users`);
  }
}

function relaySubjectToken(options, cliToken) {
  if (process.env.T3_CONNECT_SESSION_TOKEN) {
    return process.env.T3_CONNECT_SESSION_TOKEN.trim();
  }
  if (options.sessionTokenFile) {
    try {
      const tokenPath = resolve(options.sessionTokenFile);
      assertPrivateFile(tokenPath, "token file");
      return readFileSync(tokenPath, "utf8").trim();
    } catch (error) {
      throw new FleetError(`could not read --session-token-file: ${error.message}`);
    }
  }
  return cliToken;
}

function sourceDigest() {
  const verifier = join(sourceSkill, "scripts", "sync_grok_harness.py");
  try {
    const output = execFileSync(
      "python3",
      [verifier, "digest", "--source", sourceSkill, "--json"],
      {
        encoding: "utf8",
        env: childEnvironment(),
        stdio: ["ignore", "pipe", "pipe"],
      },
    );
    return JSON.parse(output).sourceDigest;
  } catch (error) {
    throw new FleetError(`could not calculate the canonical skill digest: ${error.message}`);
  }
}

function sourceReleaseCommit() {
  const git = (...arguments_) =>
    execFileSync("git", ["-C", sourceSkill, ...arguments_], {
      encoding: "utf8",
      env: childEnvironment(),
      stdio: ["ignore", "pipe", "pipe"],
    }).trim();
  try {
    if (git("status", "--porcelain")) {
      throw new Error("the canonical source checkout is dirty");
    }
    if (git("branch", "--show-current") !== "main") {
      throw new Error("the canonical source checkout is not on main");
    }
    execFileSync("git", ["-C", sourceSkill, "fetch", "--prune", "origin", "main"], {
      env: childEnvironment(),
      stdio: ["ignore", "pipe", "pipe"],
    });
    const head = git("rev-parse", "HEAD");
    if (head !== git("rev-parse", "origin/main")) {
      throw new Error("local main does not match origin/main");
    }
    return head;
  } catch (error) {
    throw new FleetError(`cannot identify an immutable fleet release: ${error.message}`);
  }
}

function selectedEnvironments(environments, requested) {
  if (requested.length === 0) return environments;
  const selected = environments.filter(
    (environment) =>
      requested.includes(environment.environmentId) || requested.includes(environment.label),
  );
  const found = new Set(
    selected.flatMap((environment) => [environment.environmentId, environment.label]),
  );
  const missing = requested.filter((value) => !found.has(value));
  if (missing.length > 0) {
    throw new FleetError(`unknown T3 environment(s): ${missing.join(", ")}`);
  }
  return selected;
}

async function main() {
  const options = parseArguments(process.argv.slice(2));
  const clerkToken = refreshAndReadClerkToken(options.baseDir);
  const environments = selectedEnvironments(
    await listEnvironments(clerkToken),
    options.environments,
  );
  if (options.command === "list") {
    console.log(
      JSON.stringify({
        schemaVersion: 1,
        environments: environments.map(({ environmentId, label, linkedAt }) => ({
          environmentId,
          label,
          linkedAt,
        })),
      }),
    );
    return;
  }
  if (environments.length === 0) throw new FleetError("no linked T3 environments found");

  const expectedDigest = sourceDigest();
  const releaseCommit = options.command === "apply" ? sourceReleaseCommit() : undefined;
  const signer = makeDpopSigner();
  let relayToken;
  try {
    relayToken = await exchangeRelayToken(relaySubjectToken(options, clerkToken), signer);
  } catch (error) {
    if (
      !options.sessionTokenFile &&
      !process.env.T3_CONNECT_SESSION_TOKEN &&
      error instanceof Error &&
      error.message.includes("invalid_bearer")
    ) {
      throw new FleetError(
        "the T3 relay accepts the CLI credential for discovery but requires an authenticated " +
          "T3 client session JWT for remote execution; sign in at app.t3.codes and provide a " +
          "short-lived t3-relay token through --session-token-file or T3_CONNECT_SESSION_TOKEN",
      );
    }
    throw error;
  }
  const settled = await Promise.allSettled(
    environments.map((environment) =>
      runInEnvironment(
        environment,
        options.command,
        releaseCommit,
        relayToken,
        signer,
        options.timeoutSeconds * 1000,
      ),
    ),
  );
  const results = settled.map((result, index) => {
    const environment = environments[index];
    if (result.status === "rejected") {
      return {
        environmentId: environment.environmentId,
        label: environment.label,
        matches: false,
        error: result.reason instanceof Error ? result.reason.message : String(result.reason),
      };
    }
    const report = result.value;
    return {
      environmentId: environment.environmentId,
      label: environment.label,
      matches: report.approved === true && report.installedDigest === expectedDigest,
      report,
    };
  });
  const fleetReport = {
    schemaVersion: 1,
    operation: options.command,
    ...(releaseCommit ? { releaseCommit } : {}),
    expectedDigest,
    approved: results.every((result) => result.matches),
    environments: results,
  };
  console.log(JSON.stringify(fleetReport));
  if (!fleetReport.approved) process.exitCode = 1;
}

if (
  process.argv[1] &&
  realpathSync(process.argv[1]) === realpathSync(fileURLToPath(import.meta.url))
) {
  main().catch((error) => {
    const message = error instanceof Error ? error.message : String(error);
    console.error(`sync-grok-t3-connect: ${message}`);
    process.exitCode = 1;
  });
}
