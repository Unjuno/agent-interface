from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

import audit
import build_fixture
import candidate


class T0ContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.fixture_path = self.root / "fixture.json"
        self.candidate_path = self.root / "candidate.json"
        self.fixture_path.write_text(json.dumps(build_fixture.make_fixture(), sort_keys=True, indent=2) + "\n")
        candidate.run(self.fixture_path, self.candidate_path)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def read_candidate(self):
        return json.loads(self.candidate_path.read_text())

    def write_candidate(self, value):
        self.candidate_path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")

    def test_clean_candidate_is_independently_reconstructed(self):
        result = audit.audit(self.fixture_path, self.candidate_path)
        self.assertEqual(result["result"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["independently_reconstructed"], 24)

    def test_matched_arms_keep_content_state_and_answer_access_equal(self):
        data = build_fixture.make_fixture()["rows"]
        grouped = {}
        for row in data:
            grouped.setdefault(row["scenario_id"], []).append(row)
        self.assertEqual(len(grouped), 6)
        for rows in grouped.values():
            self.assertEqual({r["arm"] for r in rows}, set(build_fixture.ARMS))
            self.assertEqual(len({json.dumps(r["task"], sort_keys=True) for r in rows}), 1)
            self.assertEqual(len({json.dumps(r["interrupt"], sort_keys=True) for r in rows}), 1)
            self.assertEqual(len({json.dumps(r["state"], sort_keys=True) for r in rows}), 1)

    def test_private_view_cue_authority_state_and_urgent_invariants(self):
        result = self.read_candidate()
        for display in result["displays"]:
            self.assertFalse(display["automatic_effect"])
            self.assertEqual(display["return_action"], "not_authorized_by_prompt_or_cue")
            if display["cue_display"] is not None:
                self.assertEqual(display["cue_display"]["author"], "user")
                self.assertFalse(display["cue_display"]["is_authority"])
            if display["urgent_not_delayed"]:
                self.assertEqual(display["delivery"], "immediate")
            if "changed_external_state" in display["row_id"] or "duplicate_effect_guard" in display["row_id"]:
                self.assertEqual(display["state_change_warning"], "revalidate_before_return_action")

    def test_six_frozen_output_corruptions_fail_closed(self):
        base = self.read_candidate()
        changes = {
            "swapped task or window": lambda d: d["preserved_view"].__setitem__("window_id", "other-window"),
            "stale cue after external edit": lambda d: d.__setitem__("state_change_warning", None),
            "forged agent-authored cue": lambda d: d["cue_display"].__setitem__("author", "agent"),
            "duplicate save": lambda d: d.__setitem__("automatic_effect", True),
            "cue absent in offered-and-written arm": lambda d: d.__setitem__("cue_display", None),
            "delayed emergency release": lambda d: d.__setitem__("delivery", "defer_until_user_safe_boundary"),
        }
        targets = {
            "swapped task or window": "stable_cue_written::preserved_view",
            "stale cue after external edit": "changed_external_state::preserved_view",
            "forged agent-authored cue": "stable_cue_written::preserved_view_optional_cue",
            "duplicate save": "duplicate_effect_guard::preserved_view",
            "cue absent in offered-and-written arm": "stable_cue_written::preserved_view_optional_cue",
            "delayed emergency release": "urgent_release::timing_only",
        }
        for name, mutate in changes.items():
            with self.subTest(control=name):
                altered = copy.deepcopy(base)
                display = next(row for row in altered["displays"] if row["row_id"] == targets[name])
                mutate(display)
                self.write_candidate(altered)
                self.assertEqual(audit.audit(self.fixture_path, self.candidate_path)["result"], "FAIL_METHOD")
        self.write_candidate(base)


if __name__ == "__main__":
    unittest.main()
