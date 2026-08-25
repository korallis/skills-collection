from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_grok_fleet.py"
SPEC = importlib.util.spec_from_file_location("verify_grok_fleet", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class FleetVerifierTests(unittest.TestCase):
    def test_run_json_rejects_a_non_object(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "not an object"):
            VERIFY.run_json([sys.executable, "-c", "print('[]')"])

    def test_remote_report_rejects_an_option_like_destination(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "must not start"):
            VERIFY.remote_report("-oProxyCommand=bad", 5)

    def test_main_reports_a_missing_canonical_digest_without_traceback(self) -> None:
        with (
            patch.object(VERIFY, "local_report", return_value={"approved": True}),
            patch.object(sys, "argv", [str(SCRIPT), "local"]),
            patch("builtins.print") as output,
        ):
            result = VERIFY.main()

        self.assertEqual(result, 1)
        self.assertIn("no sourceDigest", str(output.call_args_list))


if __name__ == "__main__":
    unittest.main()
