import json
import tempfile
import unittest
from pathlib import Path

import auditor
import builder
import candidate


class VisualAssumptionGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.fixture, self.oracle = builder.build(self.root)
        self.fixture_path = self.root / "fixture.json"
        self.oracle_path = self.root / "oracle.json"
        self.fixture_path.write_text(json.dumps(self.fixture), encoding="utf-8")
        self.oracle_path.write_text(json.dumps(self.oracle), encoding="utf-8")
        self.raw_path = self.root / "raw.jsonl"
        self.rows = candidate.run(self.fixture_path, self.raw_path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_twelve_rows_and_three_positive_cases(self):
        self.assertEqual(len(self.rows), 12)
        self.assertEqual(sum(x["classification"] == "CUE" for x in self.rows), 3)
        self.assertTrue(all(x["release_request"] for x in self.rows[:3]))
        self.assertTrue(all(200 <= x["release_lead_ms"] <= 900 for x in self.rows[:3]))

    def test_common_mode_visible_and_missing_assumptions_fail_closed(self):
        indexed = {x["case_id"]: x for x in self.rows}
        expected = {"k04": ("REJECT", "common_mode_zoom"),
                    "k05": ("REJECT", "off_axis_motion"),
                    "k06": ("REJECT", "shape_deformation"),
                    "k07": ("REJECT", "partial_occlusion"),
                    "k08": ("REJECT", "appearance_discontinuity"),
                    "k09": ("UNKNOWN", "missing_anchors"),
                    "k10": ("UNKNOWN", "unstable_anchors"),
                    "k11": ("UNKNOWN", "insufficient_scene_flow"),
                    "k12": ("UNKNOWN", "insufficient_scene_flow")}
        for cid, value in expected.items():
            with self.subTest(case=cid):
                self.assertEqual((indexed[cid]["classification"], indexed[cid]["reason"]), value)
                self.assertFalse(indexed[cid]["release_request"])

    def test_nonidentifiable_pair_is_pixel_and_output_identical(self):
        fixture = {x["case_id"]: x for x in self.fixture["cases"]}
        indexed = {x["case_id"]: x for x in self.rows}
        for key in ("frame0", "frame1"):
            self.assertEqual((self.root / fixture["k11"][key]).read_bytes(),
                             (self.root / fixture["k12"][key]).read_bytes())
        a, b = dict(indexed["k11"]), dict(indexed["k12"])
        a.pop("case_id"); b.pop("case_id")
        self.assertEqual(a, b)
        self.assertEqual(indexed["k11"]["classification"], "UNKNOWN")

    def test_independent_raw_audit_and_six_corruption_controls(self):
        report = auditor.audit(self.fixture_path, self.oracle_path, self.raw_path)
        self.assertEqual(report["verdict"], "PASS_METHOD_SCOPED")
        self.assertEqual(report["n_rows"], 12)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["corruption_rejected"], {
            "missing_row": True, "duplicate_row": True, "forged_frame_hash": True,
            "forged_geometry": True,
            "false_safe_control": True, "fabricated_release_lead": True})

    def test_builder_frozen_ttc_oracle_matches_image_reconstruction(self):
        result = auditor.audit(self.fixture_path, self.oracle_path, self.raw_path)
        self.assertTrue(all(result["gates"].values()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
