from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sync_grok_harness.py"
SPEC = importlib.util.spec_from_file_location("sync_grok_harness", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
SYNC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SYNC)


class GrokHarnessTests(unittest.TestCase):
    def test_digest_does_not_require_an_installation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "digest",
                    "--skills-root",
                    str(Path(directory) / "missing"),
                    "--json",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"sourceDigest"', result.stdout)

    def test_config_update_preserves_unrelated_settings(self) -> None:
        original = """[models]
default = "grok-4.6"

[ui]
compact_mode = false
permission_mode = "acceptEdits"
permission_mode_note = "preserve me"

[privacy]
acknowledged = true
"""
        expected = """[models]
default = "grok-4.6"

[ui]
permission_mode = "always-approve"
compact_mode = false
permission_mode_note = "preserve me"

[privacy]
acknowledged = true
"""
        self.assertEqual(SYNC.render_grok_config(original), expected)

    def test_config_update_ignores_section_text_inside_multiline_strings(self) -> None:
        original = '''[models]
note = """
[ui]
permission_mode = "do not interpret me"
"""

[ui] # preserve this comment
compact_mode = false
'''
        expected = '''[models]
note = """
[ui]
permission_mode = "do not interpret me"
"""

[ui] # preserve this comment
permission_mode = "always-approve"
compact_mode = false
'''
        self.assertEqual(SYNC.render_grok_config(original), expected)

    def test_config_update_preserves_permission_text_inside_ui_multiline_value(self) -> None:
        original = '''[ui]
note = """
permission_mode = "this is documentation"
"""
permission_mode = "acceptEdits"
'''
        expected = '''[ui]
permission_mode = "always-approve"
note = """
permission_mode = "this is documentation"
"""
'''
        self.assertEqual(SYNC.render_grok_config(original), expected)

    def test_install_is_idempotent_and_verifiable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skills_root = root / "skills"
            grok_config = root / ".grok" / "config.toml"
            bin_directory = root / "bin"
            grok_config.parent.mkdir(parents=True)
            grok_config.write_text("[ui]\ncompact_mode = false\n", encoding="utf-8")
            grok_config.chmod(0o600)

            first = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "install",
                    "--skills-root",
                    str(skills_root),
                    "--grok-config",
                    str(grok_config),
                    "--bin-dir",
                    str(bin_directory),
                    "--json",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            first_config = grok_config.read_bytes()
            first_digest = SYNC.tree_digest(skills_root / "lee-engineering")

            second = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "install",
                    "--skills-root",
                    str(skills_root),
                    "--grok-config",
                    str(grok_config),
                    "--bin-dir",
                    str(bin_directory),
                    "--json",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(grok_config.read_bytes(), first_config)
            self.assertEqual(grok_config.stat().st_mode & 0o777, 0o600)
            self.assertEqual(SYNC.tree_digest(skills_root / "lee-engineering"), first_digest)
            self.assertTrue((bin_directory / "lee-grok").stat().st_mode & 0o100)
            self.assertTrue((bin_directory / "lee-grok-review").stat().st_mode & 0o100)
            self.assertTrue((bin_directory / "lee-cursor-grok").stat().st_mode & 0o100)

    def test_default_install_converges_agents_and_claude_roots(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            environment = dict(os.environ)
            environment["HOME"] = str(home)
            result = subprocess.run(
                ["python3", str(SCRIPT), "install", "--json"],
                check=False,
                capture_output=True,
                text=True,
                env=environment,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            agents_skill = home / ".agents" / "skills" / "lee-engineering"
            claude_skill = home / ".claude" / "skills" / "lee-engineering"
            self.assertEqual(SYNC.tree_digest(agents_skill), SYNC.tree_digest(claude_skill))

    def test_wrapper_rejects_permission_override(self) -> None:
        wrapper = Path(__file__).resolve().parents[1] / "scripts" / "lee-grok"
        result = subprocess.run(
            [str(wrapper), "--permission-mode", "acceptEdits"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 64)
        self.assertIn("approve mode is fixed", result.stderr)

        alias_result = subprocess.run(
            [str(wrapper), "--yolo"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(alias_result.returncode, 64)
        self.assertIn("approve mode is fixed", alias_result.stderr)

    def test_wrapper_injects_approve_mode(self) -> None:
        wrapper = Path(__file__).resolve().parents[1] / "scripts" / "lee-grok"
        with tempfile.TemporaryDirectory() as directory:
            bin_directory = Path(directory)
            fake_grok = bin_directory / "grok"
            fake_grok.write_text("#!/bin/sh\nprintf '%s\\n' \"$@\"\n", encoding="utf-8")
            fake_grok.chmod(0o755)
            environment = dict(os.environ)
            environment["PATH"] = f"{bin_directory}:{environment['PATH']}"
            result = subprocess.run(
                [str(wrapper), "--model", "grok-4.6"],
                check=False,
                capture_output=True,
                text=True,
                env=environment,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.splitlines(),
            ["--always-approve", "--model", "grok-4.6"],
        )

    def test_cursor_wrapper_pins_grok_and_force(self) -> None:
        wrapper = Path(__file__).resolve().parents[1] / "scripts" / "lee-cursor-grok"
        with tempfile.TemporaryDirectory() as directory:
            bin_directory = Path(directory)
            fake_cursor = bin_directory / "cursor-agent"
            fake_cursor.write_text("#!/bin/sh\nprintf '%s\\n' \"$@\"\n", encoding="utf-8")
            fake_cursor.chmod(0o755)
            environment = dict(os.environ)
            environment["PATH"] = f"{bin_directory}:{environment['PATH']}"
            result = subprocess.run(
                [str(wrapper), "--print"],
                check=False,
                capture_output=True,
                text=True,
                env=environment,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.splitlines(),
            ["--force", "--model", "cursor-grok-4.6-xhigh", "--print"],
        )

    def test_cursor_wrapper_rejects_mode_override(self) -> None:
        wrapper = Path(__file__).resolve().parents[1] / "scripts" / "lee-cursor-grok"
        result = subprocess.run(
            [str(wrapper), "--mode", "ask"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 64)
        self.assertIn("approve mode is fixed", result.stderr)

        plan_result = subprocess.run(
            [str(wrapper), "--plan"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(plan_result.returncode, 64)
        self.assertIn("approve mode is fixed", plan_result.stderr)

        short_model_result = subprocess.run(
            [str(wrapper), "-m", "another-model"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(short_model_result.returncode, 64)
        self.assertIn("model is pinned", short_model_result.stderr)

    def test_review_wrapper_enforces_bounded_streaming_profile(self) -> None:
        wrapper = Path(__file__).resolve().parents[1] / "scripts" / "lee-grok-review"
        with tempfile.TemporaryDirectory() as directory:
            bin_directory = Path(directory)
            fake_grok = bin_directory / "grok"
            fake_grok.write_text("#!/bin/sh\nprintf '%s\\n' \"$@\"\n", encoding="utf-8")
            fake_grok.chmod(0o755)
            environment = dict(os.environ)
            environment["PATH"] = f"{bin_directory}:{environment['PATH']}"
            result = subprocess.run(
                [str(wrapper), "--single", "review this packet"],
                check=False,
                capture_output=True,
                text=True,
                env=environment,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        arguments = result.stdout.splitlines()
        self.assertIn("--always-approve", arguments)
        self.assertIn("grok-4.6", arguments)
        self.assertIn("streaming-messages-json", arguments)
        self.assertIn("--include-partial-messages", arguments)
        self.assertIn("--max-turns", arguments)
        self.assertIn("--no-plan", arguments)
        self.assertIn("--no-subagents", arguments)
        self.assertIn("--disable-web-search", arguments)
        self.assertIn("--disallowed-tools", arguments)

    def test_review_wrapper_rejects_profile_overrides(self) -> None:
        wrapper = Path(__file__).resolve().parents[1] / "scripts" / "lee-grok-review"
        for arguments in (
            ["--permission-mode", "acceptEdits"],
            ["--model", "grok-4.5"],
            ["--reasoning-effort", "xhigh"],
            ["--tools", "read_file"],
            ["--allowedTools", "Read"],
        ):
            with self.subTest(arguments=arguments):
                result = subprocess.run(
                    [str(wrapper), *arguments],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 64)
                self.assertIn("fixed review profile", result.stderr)


if __name__ == "__main__":
    unittest.main()
