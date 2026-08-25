#!/usr/bin/env python3
"""Install or verify the canonical Lee skill and Grok approve-mode harness."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import tomllib
from typing import Iterable


APPROVE_MODE = "always-approve"
IGNORED_NAMES = {".DS_Store", "__pycache__"}
WRAPPER_NAMES = ("lee-grok", "lee-grok-review", "lee-cursor-grok")


class HarnessError(RuntimeError):
    """A deterministic install or verification failure."""


def canonical_skill_directory() -> Path:
    return Path(__file__).resolve().parent.parent


def default_skills_roots() -> tuple[Path, ...]:
    home = Path.home()
    return (home / ".agents" / "skills", home / ".claude" / "skills")


def default_grok_config() -> Path:
    return Path.home() / ".grok" / "config.toml"


def default_bin_directory() -> Path:
    return Path.home() / ".local" / "bin"


def included_paths(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if any(part in IGNORED_NAMES for part in path.relative_to(root).parts):
            continue
        if path.is_file() or path.is_symlink():
            yield path


def tree_digest(root: Path) -> str:
    if not (root / "SKILL.md").is_file():
        raise HarnessError(f"not a Lee skill directory: {root}")
    digest = hashlib.sha256()
    for path in included_paths(root):
        relative = path.relative_to(root).as_posix()
        executable = bool(path.lstat().st_mode & stat.S_IXUSR)
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0x\0" if executable else b"\0-\0")
        if path.is_symlink():
            digest.update(os.readlink(path).encode("utf-8"))
        else:
            digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def replace_skill(source: Path, target: Path) -> None:
    if source.resolve() == target.resolve():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    staging_parent = Path(tempfile.mkdtemp(prefix=".lee-engineering-stage-", dir=target.parent))
    staged = staging_parent / target.name
    backup = target.with_name(f".{target.name}.backup-{os.getpid()}")
    try:
        shutil.copytree(
            source,
            staged,
            symlinks=True,
            ignore=shutil.ignore_patterns(*IGNORED_NAMES),
        )
        if target.exists() or target.is_symlink():
            if backup.exists() or backup.is_symlink():
                raise HarnessError(f"refusing existing backup path: {backup}")
            os.replace(target, backup)
        os.replace(staged, target)
        if backup.exists() or backup.is_symlink():
            if backup.is_dir() and not backup.is_symlink():
                shutil.rmtree(backup)
            else:
                backup.unlink()
    except BaseException:
        if not target.exists() and backup.exists():
            os.replace(backup, target)
        raise
    finally:
        shutil.rmtree(staging_parent, ignore_errors=True)


def toml_structure(line: str, multiline: str | None) -> tuple[str, str | None]:
    """Return non-string, non-comment TOML text and the multiline-string state."""
    visible: list[str] = []
    index = 0
    quote: str | None = None
    escaped = False
    while index < len(line):
        if multiline is not None:
            closing = line.find(multiline, index)
            if closing < 0:
                return "".join(visible), multiline
            visible.extend(" " for _ in line[index : closing + 3])
            index = closing + 3
            multiline = None
            continue
        character = line[index]
        if quote is not None:
            visible.append(" ")
            if quote == '"' and character == "\\" and not escaped:
                escaped = True
            elif character == quote and not escaped:
                quote = None
            else:
                escaped = False
            index += 1
            continue
        if character == "#":
            break
        delimiter = line[index : index + 3]
        if delimiter in ('"""', "'''"):
            visible.extend("   ")
            multiline = delimiter
            index += 3
            continue
        if character in ('"', "'"):
            visible.append(" ")
            quote = character
            escaped = False
            index += 1
            continue
        visible.append(character)
        index += 1
    return "".join(visible), multiline


def section_bounds(lines: list[str], section: str) -> tuple[int, int] | None:
    start = None
    header = f"[{section}]"
    multiline = None
    for index, line in enumerate(lines):
        structure, multiline = toml_structure(line, multiline)
        stripped = structure.strip()
        if stripped == header:
            if start is not None:
                raise HarnessError(f"duplicate TOML section {header}")
            start = index
            continue
        if start is not None and stripped.startswith("[") and stripped.endswith("]"):
            return start, index
    return None if start is None else (start, len(lines))


def toml_key_name(value: str) -> str:
    key = value.strip()
    if len(key) >= 2 and key[0] == key[-1] and key[0] in ('"', "'"):
        return key[1:-1]
    return key


def render_grok_config(original: str) -> str:
    lines = original.splitlines()
    bounds = section_bounds(lines, "ui")
    setting = f'permission_mode = "{APPROVE_MODE}"'
    if bounds is None:
        if lines and lines[-1] != "":
            lines.append("")
        lines.extend(["[ui]", setting])
    else:
        start, end = bounds
        retained = []
        multiline = None
        for line in lines[start + 1 : end]:
            structure, multiline = toml_structure(line, multiline)
            key, separator, _value = structure.partition("=")
            if separator and toml_key_name(key) == "permission_mode":
                continue
            retained.append(line)
        lines[start + 1 : end] = [setting, *retained]
    rendered = "\n".join(lines) + "\n"
    try:
        tomllib.loads(rendered)
    except tomllib.TOMLDecodeError as error:
        raise HarnessError(f"refusing to write invalid Grok TOML: {error}") from error
    return rendered


def write_atomic(path: Path, content: bytes, executable: bool | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if executable is None and path.exists():
            os.chmod(temporary, stat.S_IMODE(path.stat().st_mode))
        else:
            os.chmod(temporary, 0o755 if executable else 0o644)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def install_grok_config(path: Path) -> None:
    original = path.read_text(encoding="utf-8") if path.exists() else ""
    rendered = render_grok_config(original)
    if rendered != original:
        write_atomic(path, rendered.encode("utf-8"))


def install_wrappers(source_skill: Path, bin_directory: Path) -> tuple[Path, ...]:
    installed = []
    for name in WRAPPER_NAMES:
        source = source_skill / "scripts" / name
        if not source.is_file():
            raise HarnessError(f"missing canonical wrapper: {source}")
        target = bin_directory / name
        if (
            not target.exists()
            or target.read_bytes() != source.read_bytes()
            or not os.access(target, os.X_OK)
        ):
            write_atomic(target, source.read_bytes(), executable=True)
        installed.append(target)
    return tuple(installed)


def configured_mode(path: Path) -> str:
    if not path.is_file():
        raise HarnessError(f"missing Grok config: {path}")
    try:
        parsed = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise HarnessError(f"invalid Grok TOML: {error}") from error
    ui = parsed.get("ui")
    mode = ui.get("permission_mode") if isinstance(ui, dict) else None
    if mode != APPROVE_MODE:
        raise HarnessError(f"expected {APPROVE_MODE!r} permission_mode, found {mode!r}")
    return mode


def verification_report(
    source_skill: Path,
    skills_roots: tuple[Path, ...],
    grok_config: Path,
    bin_directory: Path,
) -> dict[str, object]:
    source_digest = tree_digest(source_skill)
    installations = []
    installed_digests = []
    for skills_root in skills_roots:
        installed_skill = skills_root / "lee-engineering"
        installed_digest = tree_digest(installed_skill)
        installed_digests.append(installed_digest)
        installations.append(
            {
                "skillsRoot": str(skills_root),
                "installed": str(installed_skill),
                "installedDigest": installed_digest,
                "skillMatches": installed_digest == source_digest,
            }
        )
    wrapper_matches = {}
    for name in WRAPPER_NAMES:
        installed_wrapper = bin_directory / name
        expected_wrapper = source_skill / "scripts" / name
        wrapper_matches[name] = (
            installed_wrapper.is_file()
            and os.access(installed_wrapper, os.X_OK)
            and installed_wrapper.read_bytes() == expected_wrapper.read_bytes()
        )
    mode = configured_mode(grok_config)
    report = {
        "schemaVersion": 1,
        "source": str(source_skill),
        "sourceDigest": source_digest,
        "installed": installations[0]["installed"],
        "installedDigest": installed_digests[0],
        "skillMatches": all(digest == source_digest for digest in installed_digests),
        "installations": installations,
        "wrappers": {name: str(bin_directory / name) for name in WRAPPER_NAMES},
        "wrapperMatches": wrapper_matches,
        "grokConfig": str(grok_config),
        "permissionMode": mode,
        "approved": (
            all(digest == source_digest for digest in installed_digests)
            and all(wrapper_matches.values())
            and mode == APPROVE_MODE
        ),
    }
    if not report["approved"]:
        raise HarnessError(json.dumps(report, sort_keys=True))
    return report


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(description=__doc__)
    argument_parser.add_argument("command", choices=("digest", "install", "verify"))
    argument_parser.add_argument("--source", type=Path, default=canonical_skill_directory())
    argument_parser.add_argument(
        "--skills-root",
        action="append",
        type=Path,
        help="Skill root to converge; repeat as needed. Defaults to the agents and Claude roots.",
    )
    argument_parser.add_argument("--grok-config", type=Path, default=default_grok_config())
    argument_parser.add_argument("--bin-dir", type=Path, default=default_bin_directory())
    argument_parser.add_argument("--json", action="store_true")
    return argument_parser


def main() -> int:
    arguments = parser().parse_args()
    source = arguments.source.expanduser().resolve()
    configured_roots = arguments.skills_root or list(default_skills_roots())
    skills_roots = []
    resolved_targets: set[Path] = set()
    for configured_root in configured_roots:
        skills_root = configured_root.expanduser()
        resolved_target = (skills_root / "lee-engineering").resolve()
        if resolved_target in resolved_targets:
            continue
        resolved_targets.add(resolved_target)
        skills_roots.append(skills_root)
    grok_config = arguments.grok_config.expanduser()
    bin_directory = arguments.bin_dir.expanduser()
    try:
        if arguments.command == "digest":
            report = {
                "schemaVersion": 1,
                "source": str(source),
                "sourceDigest": tree_digest(source),
            }
            if arguments.json:
                print(json.dumps(report, sort_keys=True))
            else:
                print(report["sourceDigest"])
            return 0
        if arguments.command == "install":
            for skills_root in skills_roots:
                replace_skill(source, skills_root / "lee-engineering")
            install_grok_config(grok_config)
            install_wrappers(source, bin_directory)
        report = verification_report(source, tuple(skills_roots), grok_config, bin_directory)
    except (HarnessError, OSError) as error:
        print(f"sync-grok-harness: {error}", file=sys.stderr)
        return 1
    if arguments.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print(f"Grok approve mode verified: {report['installedDigest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
