#!/usr/bin/env python3
"""Tests for the two executables in bin/.

Run: python3 tests/test_bin.py
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str):
    path = ROOT / "bin" / name
    spec = importlib.util.spec_from_loader(
        name.replace("-", "_"), importlib.machinery.SourceFileLoader(name.replace("-", "_"), str(path))
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ROUTES = load("agent-routes")
SKILLS = load("agent-skills")


class FamilyDerivation(unittest.TestCase):
    def test_lineage_comes_from_the_model_id(self) -> None:
        cases = {
            "claude-opus-5-thinking-high": "claude",
            "anthropic/claude-fable-5": "claude",
            "gpt-5.3-codex-xhigh": "gpt",
            "o3": "gpt",
            "gemini-3.5-flash": "gemini",
            "cursor-grok-4.6-high-fast": "grok",
            "kimi-k2": "kimi",
            "glm-4.6": "glm",
        }
        for model_id, family in cases.items():
            with self.subTest(model_id=model_id):
                self.assertEqual(ROUTES.family_of(model_id), family)

    def test_grok_composer_is_grok_not_composer(self) -> None:
        """xAI ships grok-composer-*; only Cursor's bare composer-* is its own line."""
        self.assertEqual(ROUTES.family_of("grok-composer-2.5-fast"), "grok")
        self.assertEqual(ROUTES.family_of("composer-2.5"), "composer")

    def test_unrecognised_lineage_is_unknown_not_guessed(self) -> None:
        self.assertEqual(ROUTES.family_of("mai-ds-r1"), "unknown")
        self.assertEqual(ROUTES.family_of(""), "unknown")


class FallbackMarking(unittest.TestCase):
    def routes(self) -> list[dict]:
        return [
            {"family": "claude", "sourceKind": "harness"},
            {"family": "claude", "sourceKind": "cli-fallback"},
            {"family": "glm", "sourceKind": "cli-fallback"},
        ]

    def test_cli_route_is_demoted_when_the_harness_reaches_that_family(self) -> None:
        routes = self.routes()
        ROUTES._mark_fallbacks(routes)
        self.assertIsNotNone(routes[1]["preferOver"])

    def test_cli_route_stands_when_it_is_the_only_way_to_that_family(self) -> None:
        routes = self.routes()
        ROUTES._mark_fallbacks(routes)
        self.assertIsNone(routes[2]["preferOver"])

    def test_harness_routes_are_never_demoted(self) -> None:
        routes = self.routes()
        ROUTES._mark_fallbacks(routes)
        self.assertIsNone(routes[0]["preferOver"])


class PoolState(unittest.TestCase):
    def test_unmetered_pool_is_unknown_not_available(self) -> None:
        self.assertEqual(ROUTES._pool_state(None), "unknown")

    def test_thresholds(self) -> None:
        self.assertEqual(ROUTES._pool_state(0.10), "available")
        self.assertEqual(ROUTES._pool_state(0.90), "constrained")
        self.assertEqual(ROUTES._pool_state(1.0), "exhausted")


class TextCatalogParsing(unittest.TestCase):
    def test_cursor_listing_drops_the_auto_pseudo_model(self) -> None:
        parsed = ROUTES._parse_cursor(
            "Available models\n\nauto - Auto (default)\ngpt-5.2 - GPT-5.2\ncomposer-2.5 - Composer 2.5\n"
        )
        self.assertEqual(parsed, ["gpt-5.2", "composer-2.5"])

    def test_grok_listing_reads_both_bullet_styles(self) -> None:
        parsed = ROUTES._parse_grok(
            "Available models:\n  * grok-4.6 (default)\n  - grok-4.5\n"
        )
        self.assertEqual(parsed, ["grok-4.6", "grok-4.5"])


class MissingBinaries(unittest.TestCase):
    def test_a_missing_binary_is_a_recorded_fact_not_a_crash(self) -> None:
        code, output = ROUTES.run(["definitely-not-a-real-binary-xyz"])
        self.assertEqual(code, 127)
        self.assertIn("not installed", output)


class Linking(unittest.TestCase):
    def test_link_replaces_a_copy_with_a_symlink_to_the_one_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "collection" / "demo-skill"
            source.mkdir(parents=True)
            (source / "SKILL.md").write_text("---\nname: demo-skill\n---\n", encoding="utf-8")

            root = base / "root"
            stale = root / "demo-skill"
            stale.mkdir(parents=True)
            (stale / "SKILL.md").write_text("stale copy", encoding="utf-8")

            self.assertEqual(SKILLS.classify(stale, source), "copy")
            SKILLS.link([root], [source], dry_run=False)
            self.assertTrue(stale.is_symlink())
            self.assertEqual(stale.resolve(), source.resolve())
            self.assertEqual(SKILLS.classify(stale, source), "linked")

    def test_dry_run_changes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "collection" / "demo-skill"
            source.mkdir(parents=True)
            (source / "SKILL.md").write_text("x", encoding="utf-8")
            root = base / "root"

            actions = SKILLS.link([root], [source], dry_run=True)
            self.assertEqual([item["action"] for item in actions], ["link"])
            self.assertFalse((root / "demo-skill").exists())

    def test_a_link_to_somewhere_else_is_reported_as_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "a" / "demo"
            other = base / "b" / "demo"
            for path in (source, other):
                path.mkdir(parents=True)
                (path / "SKILL.md").write_text("x", encoding="utf-8")
            root = base / "root"
            root.mkdir()
            (root / "demo").symlink_to(other, target_is_directory=True)

            self.assertEqual(SKILLS.classify(root / "demo", source), "linked-elsewhere")

    def test_only_directories_with_a_skill_file_are_skills(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            (base / "real-skill").mkdir()
            (base / "real-skill" / "SKILL.md").write_text("x", encoding="utf-8")
            (base / "bin").mkdir()
            (base / "bin" / "SKILL.md").write_text("x", encoding="utf-8")
            (base / "not-a-skill").mkdir()

            names = [path.name for path in SKILLS.skill_directories(base)]
            self.assertEqual(names, ["real-skill"])


class CollectionIntegrity(unittest.TestCase):
    def test_every_skill_directory_declares_a_matching_name(self) -> None:
        for skill in SKILLS.skill_directories(ROOT):
            with self.subTest(skill=skill.name):
                header = (skill / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn(f"name: {skill.name}", header)

    def test_scan_writes_a_readable_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "routes.json"
            environment = dict(os.environ, AGENT_ROUTES_FILE=str(target))
            result = subprocess.run(
                [sys.executable, str(ROOT / "bin" / "agent-routes"), "scan", "--json"],
                capture_output=True,
                text=True,
                env=environment,
                timeout=180,
                check=False,
            )
            self.assertTrue(target.is_file(), result.stderr)
            report = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(report["schemaVersion"], ROUTES.SCHEMA_VERSION)
            for key in ("harness", "sources", "routes", "pools", "families"):
                self.assertIn(key, report)
            for route in report["routes"]:
                self.assertIn(route["sourceKind"], ("harness", "cli-fallback"))
                self.assertTrue(route["routeId"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
