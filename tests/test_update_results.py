"""Regression tests for safe provider-result reconciliation."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "update_results.py"
SPEC = importlib.util.spec_from_file_location("update_results", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ResultReconciliationTests(unittest.TestCase):
    def test_exact_result_fills_empty_score_and_records_provenance(self):
        game = {"hg": "", "ag": ""}
        outcome = MODULE.apply_verified_result(
            game, (2, 1), verified_at="2026-11-11"
        )
        self.assertEqual(outcome, "filled")
        self.assertEqual((game["hg"], game["ag"]), (2, 1))
        self.assertEqual(game["result_source"], "api-football")
        self.assertEqual(game["result_verified_at"], "2026-11-11")

    def test_existing_matching_score_is_unchanged(self):
        game = {"hg": "2", "ag": "1", "note": "manual"}
        before = dict(game)
        self.assertEqual(MODULE.apply_verified_result(game, (2, 1)), "already")
        self.assertEqual(game, before)

    def test_conflicting_existing_score_is_never_overwritten(self):
        game = {"hg": "1", "ag": "0", "note": "manual"}
        before = dict(game)
        self.assertEqual(MODULE.apply_verified_result(game, (2, 1)), "conflict")
        self.assertEqual(game, before)

    def test_partial_existing_score_requires_manual_review(self):
        game = {"hg": "1", "ag": ""}
        before = dict(game)
        self.assertEqual(MODULE.apply_verified_result(game, (2, 1)), "incomplete")
        self.assertEqual(game, before)

    def test_none_scores_are_treated_as_missing(self):
        game = {"hg": None, "ag": None}
        self.assertEqual(MODULE.apply_verified_result(game, (0, 0)), "filled")
        self.assertEqual((game["hg"], game["ag"]), (0, 0))

    def test_result_key_normalizes_names_but_requires_same_date_and_order(self):
        key = MODULE.result_key("2026-11-11T18:00:00Z", "FC København", "AGF")
        self.assertEqual(key, ("2026-11-11", "fckbenhavn", "agf"))
        self.assertNotEqual(key, MODULE.result_key("2026-11-12", "FC København", "AGF"))
        self.assertNotEqual(key, MODULE.result_key("2026-11-11", "AGF", "FC København"))


if __name__ == "__main__":
    unittest.main()
