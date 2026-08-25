#!/usr/bin/env python3
"""Verify identical Lee/Grok installs locally and over SSH."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


REMOTE_VERIFY = "~/.agents/skills/lee-engineering/scripts/sync_grok_harness.py verify --json"


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(description=__doc__)
    argument_parser.add_argument(
        "targets",
        nargs="*",
        default=["local"],
        help="Use 'local' or an SSH destination such as lee@host.",
    )
    argument_parser.add_argument(
        "--source",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
    )
    argument_parser.add_argument("--connect-timeout", type=int, default=5)
    return argument_parser


def run_json(command: list[str]) -> dict[str, object]:
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise RuntimeError(detail)
    decoded = json.loads(result.stdout)
    if not isinstance(decoded, dict):
        raise RuntimeError("command returned JSON that is not an object")
    return decoded


def local_report(source: Path) -> dict[str, object]:
    verifier = source / "scripts" / "sync_grok_harness.py"
    return run_json([sys.executable, str(verifier), "verify", "--source", str(source), "--json"])


def remote_report(target: str, timeout: int) -> dict[str, object]:
    if target.startswith("-"):
        raise RuntimeError("SSH destination must not start with '-'")
    return run_json(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            f"ConnectTimeout={timeout}",
            target,
            "python3",
            REMOTE_VERIFY,
        ]
    )


def main() -> int:
    arguments = parser().parse_args()
    source = arguments.source.expanduser().resolve()
    try:
        expected = local_report(source)
        expected_digest = expected.get("sourceDigest")
        if not isinstance(expected_digest, str) or not expected_digest:
            raise RuntimeError("canonical report has no sourceDigest")
    except (OSError, RuntimeError, json.JSONDecodeError) as error:
        print(f"fleet verification could not establish the canonical digest: {error}", file=sys.stderr)
        return 1
    failures = []
    reports = []
    for target in arguments.targets:
        try:
            report = expected if target == "local" else remote_report(target, arguments.connect_timeout)
            matches = report.get("installedDigest") == expected_digest and report.get("approved") is True
            reports.append({"target": target, "matches": matches, "report": report})
            if not matches:
                failures.append(target)
        except (OSError, RuntimeError, json.JSONDecodeError) as error:
            reports.append({"target": target, "matches": False, "error": str(error)})
            failures.append(target)
    print(json.dumps({"schemaVersion": 1, "expectedDigest": expected_digest, "targets": reports}, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
