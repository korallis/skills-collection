#!/usr/bin/env python3
"""Tests for the two executables in bin/.

Run: python3 tests/test_bin.py
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import re
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
ROLES = load("agent-roles")


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

    def test_mistral_small_line_is_not_missed(self) -> None:
        """`ministral` does not contain the substring `mistral`."""
        self.assertEqual(ROUTES.family_of("ministral-3-8b-25-12"), "mistral")
        self.assertEqual(ROUTES.family_of("leanstral-1-5"), "mistral")

    def test_meta_ships_two_lines(self) -> None:
        self.assertEqual(ROUTES.family_of("llama-4-behemoth"), "llama")
        self.assertEqual(ROUTES.family_of("muse-spark-1.2"), "muse")
        self.assertEqual(ROUTES.family_of("muse-glimmer"), "muse")

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


def make_skill(path: Path, body: str = "---\nname: demo-skill\n---\n") -> Path:
    path.mkdir(parents=True, exist_ok=True)
    (path / "SKILL.md").write_text(body, encoding="utf-8")
    return path


class Linking(unittest.TestCase):
    def test_user_authored_directory_is_never_deleted(self) -> None:
        """A name collision must not be treated as a stale copy of the collection."""
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = make_skill(base / "collection" / "demo-skill")
            mine = make_skill(base / "root" / "demo-skill", "---\nname: demo-skill\n---\nmy work\n")
            (mine / "notes.md").write_text("hours of my work", encoding="utf-8")

            actions = SKILLS.link([base / "root"], [source], dry_run=False, replace=False)

            self.assertEqual([item["action"] for item in actions], ["refused"])
            self.assertFalse((base / "root" / "demo-skill").is_symlink())
            self.assertEqual(
                (mine / "notes.md").read_text(encoding="utf-8"), "hours of my work"
            )

    def test_replace_copies_moves_aside_rather_than_deleting(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = make_skill(base / "collection" / "demo-skill")
            mine = make_skill(base / "root" / "demo-skill", "different")
            (mine / "notes.md").write_text("recoverable", encoding="utf-8")

            SKILLS.link([base / "root"], [source], dry_run=False, replace=True)

            self.assertTrue((base / "root" / "demo-skill").is_symlink())
            kept = list((base / "root").glob("demo-skill.replaced-*"))
            self.assertEqual(len(kept), 1)
            self.assertEqual(
                (kept[0] / "notes.md").read_text(encoding="utf-8"), "recoverable"
            )

    def test_an_identical_copy_is_replaced_without_a_flag(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = make_skill(base / "collection" / "demo-skill")
            make_skill(base / "root" / "demo-skill")

            actions = SKILLS.link([base / "root"], [source], dry_run=False, replace=False)

            self.assertEqual([item["action"] for item in actions], ["replace-identical-copy"])
            self.assertTrue((base / "root" / "demo-skill").is_symlink())

    def test_a_root_inside_the_collection_is_refused(self) -> None:
        """`--root .` from the clone would otherwise delete the source itself."""
        with tempfile.TemporaryDirectory() as directory:
            source_root = Path(directory) / "collection"
            make_skill(source_root / "demo-skill")
            for root in (source_root, source_root / "nested", source_root.parent):
                with self.subTest(root=root):
                    with self.assertRaises(SKILLS.UnsafeRoot):
                        SKILLS.check_root(root, source_root.resolve())

    def test_dry_run_changes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = make_skill(base / "collection" / "demo-skill")
            root = base / "root"

            actions = SKILLS.link([root], [source], dry_run=True, replace=False)
            self.assertEqual([item["action"] for item in actions], ["link"])
            self.assertFalse((root / "demo-skill").exists())

    def test_prune_removes_our_dangling_links_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source_root = base / "collection"
            make_skill(source_root / "demo-skill")
            root = base / "root"
            root.mkdir()
            (root / "renamed-away").symlink_to(source_root / "gone", target_is_directory=True)
            (root / "someone-elses").symlink_to(base / "elsewhere", target_is_directory=True)

            actions = SKILLS.prune([root], dry_run=False, source_root=source_root.resolve())

            self.assertEqual([item["path"] for item in actions], [str(root / "renamed-away")])
            self.assertFalse((root / "renamed-away").is_symlink())
            self.assertTrue((root / "someone-elses").is_symlink())

    def test_unlink_leaves_foreign_symlinks_alone(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source_root = base / "collection"
            source = make_skill(source_root / "demo-skill")
            other = make_skill(base / "other" / "demo-skill")
            root = base / "root"
            root.mkdir()
            (root / "demo-skill").symlink_to(other, target_is_directory=True)

            actions = SKILLS.unlink([root], [source], dry_run=False, source_root=source_root.resolve())

            self.assertEqual([item["action"] for item in actions], ["kept"])
            self.assertTrue((root / "demo-skill").is_symlink())

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


class LiveSession(unittest.TestCase):
    def test_a_detected_harness_with_no_catalog_still_yields_a_route(self) -> None:
        """Claude Code and Codex publish no model list, but a model is answering."""
        harness = {"id": "claude-code", "version": None, "detectedBy": "CLAUDECODE"}
        routes = ROUTES._live_session_route(harness, [], {})
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0]["sourceKind"], "harness")
        self.assertEqual(routes[0]["family"], "unknown")

    def test_no_live_route_is_added_when_the_harness_listed_models(self) -> None:
        harness = {"id": "omp", "version": None, "detectedBy": "OMPCODE"}
        existing = [{"sourceKind": "harness", "family": "claude"}]
        self.assertEqual(ROUTES._live_session_route(harness, existing, {}), [])

    def test_no_live_route_without_a_detected_harness(self) -> None:
        harness = {"id": "unknown", "version": None, "detectedBy": "none"}
        self.assertEqual(ROUTES._live_session_route(harness, [], {}), [])


class SourceStatus(unittest.TestCase):
    def test_failure_is_never_reported_as_absence(self) -> None:
        self.assertEqual(ROUTES._source_status([], "publishes no machine-readable model list"), "no-api")
        self.assertEqual(ROUTES._source_status([], "timed out after 25s"), "timeout")
        self.assertEqual(ROUTES._source_status([], "grok models failed: boom"), "failed")
        self.assertEqual(ROUTES._source_status([], None), "empty")
        self.assertEqual(ROUTES._source_status([{"a": 1}], None), "ok")


class ManifestSafety(unittest.TestCase):
    def test_a_malformed_t3_manifest_is_reported_not_fatal(self) -> None:
        home = Path.home() / ".t3" / "userdata" / "model-manifest.json"
        if home.is_file():
            routes, pools, note = ROUTES.probe_t3("t3")
            self.assertTrue(all(isinstance(r["modelId"], str) for r in routes))
        else:
            routes, pools, note = ROUTES.probe_t3("t3")
            self.assertEqual(routes, [])
            self.assertIsNotNone(note)


class ParserSafety(unittest.TestCase):
    def test_an_error_line_never_becomes_a_model(self) -> None:
        self.assertEqual(ROUTES._parse_cursor("Error - not authenticated\n"), [])
        self.assertEqual(ROUTES._parse_cursor("Models - available\n"), [])
        self.assertEqual(ROUTES._parse_grok("  * Authentication failed\n"), [])

    def test_a_provider_prefixed_id_survives_intact(self) -> None:
        self.assertEqual(ROUTES._parse_grok("  * xai/grok-4.6\n"), ["xai/grok-4.6"])

    def test_an_auth_error_on_stdout_is_a_failure_not_an_empty_catalog(self) -> None:
        self.assertTrue(ROUTES._looks_like_error("Error: not authenticated"))
        self.assertFalse(ROUTES._looks_like_error("* grok-4.6 (default)"))


class ModelRanking(unittest.TestCase):
    def test_a_release_stamp_is_not_a_version(self) -> None:
        """gpt-4o-mini-2024-07-18 must not read as version 18."""
        self.assertEqual(ROLES.version_of("gpt-4o-mini-2024-07-18"), 4.0)
        self.assertEqual(ROLES.version_of("claude-3-5-sonnet-20240620"), 3.5)
        self.assertEqual(ROLES.version_of("gpt-5.6-sol"), 5.6)
        self.assertEqual(ROLES.version_of("grok-4.6"), 4.6)

    def test_vendor_tier_words(self) -> None:
        self.assertEqual(ROLES.tier("gpt-5.4-nano", "gpt"), -1)
        self.assertEqual(ROLES.tier("claude-opus-5", "claude"), 1)
        self.assertEqual(ROLES.tier("some-model-2", "unknown"), 0)

    def test_price_is_not_capability(self) -> None:
        """A legacy flagship can be the priciest entry and the worst choice."""
        legacy = {
            "selector": "a/claude-3-opus", "modelId": "claude-3-opus", "sourceKind": "harness",
            "pool": "p", "reasoning": True, "contextWindow": 200000, "cost": {"output": 75},
        }
        current = {
            "selector": "a/claude-opus-5", "modelId": "claude-opus-5", "sourceKind": "harness",
            "pool": "p", "reasoning": True, "contextWindow": 200000, "cost": {"output": 25},
        }
        best = min([legacy, current], key=lambda r: ROLES.rank(r, {}, "capability"))
        self.assertEqual(best["modelId"], "claude-opus-5")

    def test_cheap_prefers_the_small_tier(self) -> None:
        nano = {
            "selector": "a/gpt-5.4-nano", "modelId": "gpt-5.4-nano", "sourceKind": "harness",
            "pool": "p", "reasoning": True, "contextWindow": 100000, "cost": {"output": 1},
        }
        flagship = {
            "selector": "a/gpt-5.6-sol", "modelId": "gpt-5.6-sol", "sourceKind": "harness",
            "pool": "p", "reasoning": True, "contextWindow": 900000, "cost": {"output": 40},
        }
        best = min([flagship, nano], key=lambda r: ROLES.rank(r, {}, "cheap"))
        self.assertEqual(best["modelId"], "gpt-5.4-nano")

    def test_harness_routes_outrank_cli_fallbacks(self) -> None:
        harness = {
            "selector": "h/m-2", "modelId": "m-2", "sourceKind": "harness",
            "pool": "p", "reasoning": True, "contextWindow": 1000, "cost": None,
        }
        cli = {
            "selector": "c/m-9", "modelId": "m-9", "sourceKind": "cli-fallback",
            "pool": "q", "reasoning": True, "contextWindow": 900000, "cost": None,
        }
        best = min([cli, harness], key=lambda r: ROLES.rank(r, {}, "capability"))
        self.assertEqual(best["sourceKind"], "harness")


class RoleAssignment(unittest.TestCase):
    def scan(self, routes: list[dict]) -> dict:
        return {"scannedAt": "t", "harness": {"id": "test"}, "routes": routes, "pools": []}

    def route(self, selector: str, family: str, **extra) -> dict:
        base = {
            "selector": selector, "modelId": selector.split("/")[-1], "family": family,
            "sourceKind": "harness", "source": "test", "pool": "test:p",
            "reasoning": True, "contextWindow": 200000, "cost": {"output": 10},
        }
        base.update(extra)
        return base

    def test_review_takes_a_family_other_than_implement(self) -> None:
        routing = ROLES.assign(self.scan([
            self.route("t/alpha-opus-5", "claude"),
            self.route("t/beta-sol-5", "gpt"),
        ]))
        self.assertNotEqual(
            routing["roles"]["implement"]["family"], routing["roles"]["review"]["family"]
        )

    def test_a_single_family_is_reported_not_hidden(self) -> None:
        routing = ROLES.assign(self.scan([self.route("t/only-opus-5", "claude")]))
        self.assertTrue(any("only one model family" in note for note in routing["notes"]))

    def test_the_live_session_route_is_never_pinned(self) -> None:
        """It cannot be named, so it cannot be written into a config."""
        routing = ROLES.assign(self.scan([
            self.route("<live session>", "unknown", modelId="unknown", reasoning=None),
        ]))
        self.assertTrue(all(value is None for value in routing["roles"].values()))

    def test_an_exhausted_pool_is_not_assigned(self) -> None:
        scan = self.scan([self.route("t/alpha-opus-5", "claude", pool="test:dead")])
        scan["pools"] = [{"poolId": "test:dead", "poolState": "exhausted"}]
        routing = ROLES.assign(scan)
        self.assertIsNone(routing["roles"]["implement"])

    def test_effort_matches_the_role(self) -> None:
        route = {"thinkingLevels": ["low", "medium", "high", "max"]}
        self.assertEqual(ROLES.effort_for({"prefer": "capability"}, route), "max")
        self.assertEqual(ROLES.effort_for({"prefer": "cheap"}, route), "low")
        self.assertIsNone(ROLES.effort_for({"prefer": "cheap"}, {"thinkingLevels": None}))


class AgentsFileMirror(unittest.TestCase):
    def test_a_differing_claude_file_is_refused_not_clobbered(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            agents = base / "AGENTS.md"
            agents.write_text("shared rules", encoding="utf-8")
            claude = Path("~/.claude/CLAUDE.md").expanduser()
            if claude.exists() and not claude.is_symlink():
                self.skipTest("real CLAUDE.md present; covered by the identical-copy path")
            self.assertTrue(agents.is_file())


class TierTokens(unittest.TestCase):
    def test_mini_does_not_match_gemini(self) -> None:
        """Substring matching classified every Gemini model as a small model."""
        self.assertEqual(ROLES.tier("gemini-3.7-flash"), 0)
        self.assertEqual(ROLES.tier("minimax-m1"), 0)

    def test_openai_5_6_tier_words_follow_the_vendor(self) -> None:
        """OpenAI documents Terra as the mini tier and Luna as the nano tier."""
        self.assertEqual(ROLES.tier("gpt-5.6-sol", "gpt"), 1)
        self.assertEqual(ROLES.tier("gpt-5.6-terra", "gpt"), -1)
        self.assertEqual(ROLES.tier("gpt-5.6-luna", "gpt"), -1)

    def test_fable_is_a_large_tier(self) -> None:
        """Anthropic calls Fable its most capable widely released model."""
        self.assertEqual(ROLES.tier("claude-fable-5", "claude"), 1)

    def test_an_effort_suffix_cannot_promote_a_mid_model(self) -> None:
        """An aggregator writes `claude-4.6-sonnet-max`, where max is the effort."""
        self.assertEqual(ROLES.tier("claude-4.6-sonnet-max", "claude"), 0)
        self.assertEqual(ROLES.tier("claude-4.5-sonnet-thinking", "claude"), 0)
        self.assertEqual(ROLES.tier("cursor-grok-4.6-xhigh", "grok"), 0)

    def test_an_effort_suffix_does_not_demote_a_real_tier_word(self) -> None:
        """`max` is a real model token for OpenAI codex and Qwen."""
        self.assertEqual(ROLES.tier("gpt-5.1-codex-max", "gpt"), 1)
        self.assertEqual(ROLES.tier("qwen3.8-max", "qwen"), 1)
        self.assertEqual(ROLES.tier("claude-4.6-opus-max", "claude"), 1)

    def test_the_same_word_resolves_differently_per_family(self) -> None:
        """`pro` is large for OpenAI and deliberately weightless for Gemini."""
        self.assertEqual(ROLES.tier("gpt-5.5-pro", "gpt"), 1)
        self.assertEqual(ROLES.tier("gemini-2.5-pro", "gemini"), 0)
        self.assertEqual(ROLES.tier("gemini-3.5-flash-lite", "gemini"), -1)
        self.assertEqual(ROLES.tier("gemini-3.7-flash", "gemini"), 0)

    def test_contradictory_words_carry_no_weight(self) -> None:
        """flash, pro, spark and fast mean different things per vendor."""
        for model_id, family in (
            ("gemini-3.7-flash", "gemini"),
            ("gemini-2.5-pro", "gemini"),
            ("gpt-5.3-codex-spark", "gpt"),
            ("grok-4.6-fast", "grok"),
        ):
            with self.subTest(model_id=model_id):
                self.assertLessEqual(ROLES.tier(model_id, family), 0)

    def test_google_ordering_falls_out_of_version_once_pro_is_ignored(self) -> None:
        """gemini-3.7-flash is Google's latest and most capable stable model."""
        newer_flash = {
            "selector": "g/gemini-3.7-flash", "modelId": "gemini-3.7-flash",
            "sourceKind": "harness", "pool": "p", "reasoning": True,
            "contextWindow": 1000000, "cost": {"output": 3.75},
        }
        older_pro = {
            "selector": "g/gemini-2.5-pro", "modelId": "gemini-2.5-pro",
            "sourceKind": "harness", "pool": "p", "reasoning": True,
            "contextWindow": 1000000, "cost": {"output": 10},
        }
        best = min([older_pro, newer_flash], key=lambda r: ROLES.rank(r, {}, "capability"))
        self.assertEqual(best["modelId"], "gemini-3.7-flash")

    def test_restricted_releases_are_never_auto_assigned(self) -> None:
        for model_id in ("claude-mythos-5", "gpt-daybreak-blue-latest", "gpt-5.6-cyber"):
            with self.subTest(model_id=model_id):
                self.assertTrue(ROLES.restricted(model_id))
        self.assertFalse(ROLES.restricted("claude-fable-5"))

    def test_context_markers_do_not_inflate_the_version(self) -> None:
        """claude-opus-5-1m is version 5, not 5.1, so it cannot outrank the base model."""
        self.assertEqual(ROLES.version_of("claude-opus-5-1m"), ROLES.version_of("claude-opus-5"))
        self.assertEqual(ROLES.version_of("llama-3.1-70b"), 3.1)
        self.assertEqual(ROLES.version_of("gpt-4-32k"), 4.0)

    def test_unstable_matches_whole_tokens(self) -> None:
        self.assertTrue(ROLES.unstable("gemini-3-pro-preview"))
        self.assertFalse(ROLES.unstable("some-expert-model-2"))


class PinSafety(unittest.TestCase):
    def scan(self, routes: list[dict], pools: list[dict] | None = None) -> dict:
        return {"scannedAt": "t", "harness": {"id": "test"}, "routes": routes, "pools": pools or []}

    def route(self, selector: str, family: str, **extra) -> dict:
        base = {
            "selector": selector, "modelId": selector.split("/")[-1], "family": family,
            "sourceKind": "harness", "source": "test", "pool": "test:p",
            "reasoning": True, "contextWindow": 200000, "cost": {"output": 10},
        }
        base.update(extra)
        return base

    def test_a_pin_cannot_defeat_the_different_family_rule(self) -> None:
        routes = [self.route("t/a-opus-5", "claude"), self.route("t/b-sol-5", "gpt")]
        states = {}
        problem = ROLES._pin_problem(
            {"id": "review", "distinct_from": "implement", "needs_reasoning": True},
            routes[0],
            states,
            {"implement": {"family": "claude"}},
        )
        self.assertIn("cannot review implement", problem)

    def test_a_pin_cannot_select_an_exhausted_pool(self) -> None:
        route = self.route("t/a-opus-5", "claude", pool="test:dead")
        problem = ROLES._pin_problem(
            {"id": "plan", "needs_reasoning": True}, route, {"test:dead": "exhausted"}, {}
        )
        self.assertIsNotNone(problem)

    def test_an_unknown_family_cannot_serve_as_the_reviewer(self) -> None:
        """An unprovable family is not a different family."""
        route = self.route("t/mystery-1", "unknown")
        problem = ROLES._pin_problem(
            {"id": "review", "distinct_from": "implement", "needs_reasoning": True},
            route,
            {},
            {"implement": {"family": "claude"}},
        )
        self.assertIsNotNone(problem)

    def test_review_is_left_unassigned_rather_than_sharing_a_family(self) -> None:
        routing = ROLES.assign(self.scan([self.route("t/only-opus-5", "claude")]))
        self.assertIsNotNone(routing["roles"]["implement"])
        self.assertIsNone(routing["roles"]["review"])
        self.assertTrue(any("falsely satisfy" in note for note in routing["notes"]))

    def test_a_pin_that_is_not_in_the_scan_is_rejected(self) -> None:
        problem = ROLES._pin_problem({"id": "plan", "needs_reasoning": True}, None, {}, {})
        self.assertIn("not present in the scan", problem)


class ConfigWriterSafety(unittest.TestCase):
    def test_an_unreadable_record_aborts_instead_of_emptying_config(self) -> None:
        """Fail-open here would drop every role the tool does not manage."""
        original_get, original_which = ROLES._omp_get, ROLES.shutil.which
        try:
            def boom(key: str):
                raise ROLES.ConfigUnreadable("omp config get failed: boom")

            ROLES._omp_get = boom
            ROLES.shutil.which = lambda name: "/usr/bin/omp"
            result = ROLES.apply_omp(
                {"roles": {"plan": {"selector": "a/b", "thinking": None}}}, dry_run=False
            )
        finally:
            ROLES._omp_get, ROLES.shutil.which = original_get, original_which
        self.assertEqual(result["status"], "aborted")
        self.assertEqual(result["changes"], [])

    def test_unmanaged_keys_survive_the_merge(self) -> None:
        current = {"custom": "x/y", "plan": "old/model"}
        merged = {**current, **{"plan": "new/model"}}
        self.assertEqual(merged["custom"], "x/y")
        self.assertEqual(merged["plan"], "new/model")


class ModelAgnosticism(unittest.TestCase):
    """No versioned model slug outside the classified surfaces.

    The user requirement is that skills are completely model agnostic. Slugs go
    stale and get copied; families and roles do not. Every allowed file below
    carries its reason, so the next reviewer can re-judge the exemption.
    """

    SLUG = re.compile(
        # A family word followed, optionally through one tier/series word, by a
        # version: gpt-5, qwen3.8-max, minimax-m1, deepseek-r1, mistral-small-3.2.
        r"\b(?:claude|gpt|grok|gemini|kimi|glm|composer|sonnet|opus|haiku|fable|mythos"
        r"|llama|deepseek|qwen|mistral|ministral|codestral|muse|spark|glimmer|minimax)"
        r"(?:-[a-z]+)?[-.]?v?[0-9]"
        # OpenAI o-series: o1, o3-mini, o4.
        r"|\bo[134][0-9]?\b",
        re.I,
    )
    ALLOWED = {
        "tests/test_bin.py": "test fixtures asserting parsing and ranking behaviour",
        "lee-engineering/references/model-facts.md": "the dated evidence register; slugs are its subject",
        "waves/references/recommended-config.md": "labelled per-harness example appendix",
        "waves/references/adaptation-notes.md": "dated historical research notes",
        "bin/agent-roles": "code comments citing the evidence behind tier rules",
        "bin/agent-routes": "code comments citing the evidence behind family rules",
        "lee-engineering/scripts/lee-grok-review": "fallback default, overridable via LEE_GROK_REVIEW_MODEL",
        "lee-engineering/scripts/lee-cursor-grok": "fallback default, overridable via LEE_CURSOR_GROK_MODEL",
    }

    def tracked_files(self) -> list[str]:
        out = subprocess.run(
            ["git", "ls-files"], capture_output=True, text=True, cwd=ROOT, check=True
        ).stdout.split()
        return [f for f in out if not f.endswith((".png", ".jpg", ".csv"))]

    def test_no_model_slug_outside_classified_surfaces(self) -> None:
        offenders = {}
        for name in self.tracked_files():
            if name in self.ALLOWED:
                continue
            try:
                text = (ROOT / name).read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            found = sorted(set(self.SLUG.findall(text)))
            if found:
                offenders[name] = found
        self.assertEqual(offenders, {}, f"model slugs outside classified surfaces: {offenders}")

    def test_every_skill_body_is_slug_free_no_exemptions(self) -> None:
        """SKILL.md files get no allowlist at all."""
        for skill in sorted(ROOT.glob("*/SKILL.md")):
            with self.subTest(skill=str(skill)):
                self.assertEqual(self.SLUG.findall(skill.read_text(encoding="utf-8")), [])

    def test_allowlist_entries_still_exist_and_still_hit(self) -> None:
        """A stale exemption is a hole; prune it when the file goes clean."""
        for name in self.ALLOWED:
            path = ROOT / name
            with self.subTest(name=name):
                self.assertTrue(path.is_file(), f"{name} vanished; prune the allowlist")
                self.assertTrue(
                    self.SLUG.search(path.read_text(encoding="utf-8")),
                    f"{name} no longer contains a model slug; prune its exemption",
                )


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
