import hashlib
import json
import unittest
from pathlib import Path

import audit


ROOT = Path(__file__).parent
SPEC_BYTES = (ROOT / "spec.json").read_bytes()
SPEC = json.loads(SPEC_BYTES)
SPEC_SHA = hashlib.sha256(SPEC_BYTES).hexdigest()


def fixture_raw():
    rows = []
    for scenario in SPEC["scenarios"]:
        points = scenario["trace"]
        events = [{"seq": 0, "type": "down", "x": points[0][0], "y": points[0][1], "trusted": True}]
        events.extend({"seq": i, "type": "move", "x": p[0], "y": p[1], "trusted": True}
                      for i, p in enumerate(points[1:], start=1))
        events.append({"seq": len(points), "type": "up", "x": points[-1][0], "y": points[-1][1], "trusted": True})
        first_exit = None
        validity = "NOT_APPLICABLE" if scenario["mode"] == "unconstrained" else "VALID"
        if scenario["mode"] == "constrained":
            trajectory = [(e["x"], e["y"]) for e in events[:-1]]
            gap = audit._first_gap(trajectory[0], trajectory[0], scenario["corridor_polygons"])
            if gap is not None:
                first_exit, validity = {"seq": 0, "t": 0.0}, "INVALID"
            for index, (a, b) in enumerate(zip(trajectory, trajectory[1:]), start=1):
                if first_exit is not None:
                    break
                gap = audit._first_gap(a, b, scenario["corridor_polygons"])
                if gap is not None:
                    first_exit, validity = {"seq": index, "t": gap}, "INVALID"
        endpoint = points[-1]
        endpoint_hit = ((events[-1]["x"] - endpoint[0]) ** 2 + (events[-1]["y"] - endpoint[1]) ** 2) ** 0.5 <= SPEC["endpoint_tolerance"]
        rows.append({"scenario_id": scenario["id"], "raw_events": events, "app_receipt": {
            "endpoint_hit": endpoint_hit,
            "saved_effect": endpoint_hit and validity in ("VALID", "NOT_APPLICABLE"),
            "path_validity": validity,
            "first_exit": first_exit,
        }})
    return {"schema": "path-width-gui-raw-v1", "allocation_id": "PATH-WIDTH-CONTINUOUS-GUI-6581-T0B-20261002-01",
            "run_role": "formal",
            "fixture_spec_sha256": SPEC_SHA, "fixture_html_sha256": "0" * 64,
            "browser": {"name": "Chromium", "version": "test", "platform": "linux", "arch": "arm64"},
            "scenarios": rows}


class GeometryContract(unittest.TestCase):
    def test_primary_width_pair_shares_exact_input_and_endpoint_but_effect_differs(self):
        raw = fixture_raw()
        result = audit.audit_payload(raw, SPEC, SPEC_BYTES, SPEC_SHA)
        self.assertEqual(result["disposition"], "PASS_METHOD_SCOPED", result["errors"])
        self.assertEqual(raw["scenarios"][0]["raw_events"], raw["scenarios"][1]["raw_events"])
        self.assertTrue(result["controls"]["primary_width_effect_divergence"])

    def test_segment_exit_cannot_be_erased_by_later_endpoint_hit(self):
        raw = fixture_raw()
        result = audit.audit_payload(raw, SPEC, SPEC_BYTES, SPEC_SHA)
        receipt = result["scenario_receipts"]["endpoint_after_exit"]
        self.assertTrue(receipt["endpoint_hit"])
        self.assertEqual(receipt["path_validity"], "INVALID")
        self.assertFalse(receipt["saved_effect"])
        self.assertGreater(receipt["first_exit"]["t"], 0)

    def test_corner_union_covers_each_declared_swept_segment(self):
        corridor = SPEC["scenarios"][3]["corridor_polygons"]
        self.assertIsNone(audit._first_gap((40, 30), (60, 30), corridor))
        self.assertIsNone(audit._first_gap((60, 30), (60, 70), corridor))

    def test_no_corridor_is_not_applicable_not_inferred(self):
        result = audit.audit_payload(fixture_raw(), SPEC, SPEC_BYTES, SPEC_SHA)
        receipt = result["scenario_receipts"]["ordinary_drag_no_corridor"]
        self.assertEqual(receipt["path_validity"], "NOT_APPLICABLE")
        self.assertTrue(receipt["saved_effect"])

    def test_rejects_missing_event(self):
        raw = fixture_raw()
        raw["scenarios"][1]["raw_events"].pop(2)
        self.assertNotEqual(audit.audit_payload(raw, SPEC, SPEC_BYTES, SPEC_SHA)["disposition"], "PASS_METHOD_SCOPED")

    def test_rejects_reordered_events(self):
        raw = fixture_raw()
        raw["scenarios"][0]["raw_events"][1], raw["scenarios"][0]["raw_events"][2] = raw["scenarios"][0]["raw_events"][2], raw["scenarios"][0]["raw_events"][1]
        self.assertNotEqual(audit.audit_payload(raw, SPEC, SPEC_BYTES, SPEC_SHA)["disposition"], "PASS_METHOD_SCOPED")

    def test_rejects_geometry_digest_change(self):
        raw = fixture_raw()
        changed = json.loads(SPEC_BYTES)
        changed["scenarios"][0]["corridor_polygons"][0][0][1] += 1
        changed_bytes = json.dumps(changed).encode()
        self.assertNotEqual(audit.audit_payload(raw, changed, changed_bytes, SPEC_SHA)["disposition"], "PASS_METHOD_SCOPED")

    def test_rejects_false_saved_effect_receipt(self):
        raw = fixture_raw()
        raw["scenarios"][4]["app_receipt"]["saved_effect"] = True
        self.assertNotEqual(audit.audit_payload(raw, SPEC, SPEC_BYTES, SPEC_SHA)["disposition"], "PASS_METHOD_SCOPED")

    def test_rejects_false_path_classification(self):
        raw = fixture_raw()
        raw["scenarios"][5]["app_receipt"]["path_validity"] = "VALID"
        self.assertNotEqual(audit.audit_payload(raw, SPEC, SPEC_BYTES, SPEC_SHA)["disposition"], "PASS_METHOD_SCOPED")


if __name__ == "__main__":
    unittest.main()
