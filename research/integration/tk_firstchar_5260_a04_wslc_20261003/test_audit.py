"""Independent literal corruption controls, before audit correction."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import inspect as inspect_module
import audit
from audit import inspect


def packet(root):
    fixture = {"schema": "issue5260-firstchar-a01-v1", "allocation": "test-only",
        "seed": 1, "replicates_per_cell": 1,
        "coordinate_methods": ["CHILD_ROOT_COORD"], "first_key_delay_ms": [0],
        "load_conditions": ["idle"], "payload": "hxy"}
    geometry = {"root_id": 1, "target_id": 2, "root_x": 80, "root_y": 70,
        "root_width": 520, "root_height": 250, "target_x": 16, "target_y": 87,
        "target_root_x": 96, "target_root_y": 157, "target_width": 366,
        "target_height": 23}
    rowdir = root / "row-000"
    rowdir.mkdir()
    for name, data in [("baseline.xwd", b"baseline"), ("first_visual.xwd", b"frame")]:
        (rowdir / name).write_bytes(data)
    baseline = {"exit": 0, "bytes": 8,
        "sha256": hashlib.sha256(b"baseline").hexdigest()}
    frame = {"exit": 0, "bytes": 5,
        "sha256": hashlib.sha256(b"frame").hexdigest()}
    ready = {"geometry": geometry, "ready_ns": 30,
        "readiness": {"scheduled": 1, "focus_callbacks": 1, "finalizations": 1},
        "map_configure_events": [{"kind": "Map", "monotonic_ns": 10},
                                {"kind": "Configure", "monotonic_ns": 20}],
        "baseline_frame": baseline}
    app = {"saved_text": "hxy", "save_count": 1, "first_key_ns": 60,
        "pid": 12, "geometry": geometry, "baseline_frame": baseline, "ready_ns": 30,
        "readiness": ready["readiness"], "ready_snapshot": copy.deepcopy(ready),
        "events": [{"kind": "KeyPress", "widget": "target", "char": "h",
                    "monotonic_ns": 60}],
        "first_visual": {"widget": "target", "observed_ns": 70,
                         "frame": frame, "target_value": "h"}}
    raw = {"schema": fixture["schema"], "allocation": "test-only",
        "fixture": fixture, "schedule": [{"coordinate_method": "CHILD_ROOT_COORD",
        "first_key_delay_ms": 0, "load": "idle", "replicate": 0}],
        "row_count": 1, "rows_completed": 1, "rows": [{
        "index": 0, "coordinate_method": "CHILD_ROOT_COORD", "first_key_delay_ms": 0,
        "load": "idle", "replicate": 0, "app_exit": 0, "app_parse_error": None,
        "app": app, "ready": ready, "app_pid": 12,
        "worker": {"pid": None, "exit": None},
        "injection": {"addressed_id": 2, "x": 279, "y": 168,
            "click_started_ns": 40, "click_sync_returned_ns": 50,
            "key_requests": [{"char": "h", "request_started_ns": 60},
                             {"char": "x", "request_started_ns": 80},
                             {"char": "y", "request_started_ns": 100}]}}]}
    bind_records(raw, root)
    return raw


def bind_records(raw, root):
    for row in raw["rows"]:
        row["app_stdout"] = json.dumps(row["app"]) + "\n"
        directory = root / f"row-{row['index']:03d}"
        (directory / "app_result.json").write_text(json.dumps(row["app"]), encoding="utf-8")
        (directory / "ready.json").write_text(json.dumps(row["ready"]), encoding="utf-8")


class AuditTests(unittest.TestCase):
    def run_case(self, mutation=None):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            raw = packet(root)
            if mutation:
                mutation(raw, root)
            bind_records(raw, root)
            path = root / "candidate_stdout.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            return inspect(path, root, image_audit=False)

    def test_literal_baseline_is_accepted(self):
        result = self.run_case()
        self.assertEqual(result["status"], "PASS_AUDIT", result["errors"])

    def test_ready_snapshot_drift_is_rejected_before_qualification(self):
        result = self.run_case(lambda r, p: r["rows"][0]["ready"].update(ready_ns=31))
        self.assertIn("row_0_readiness:app_ready_snapshot", result["errors"])

    def test_final_ready_file_overwrite_is_rejected(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            raw = packet(root)
            changed = {**raw["rows"][0]["ready"], "ready_ns": 31}
            (root / "row-000/ready.json").write_text(json.dumps(changed), encoding="utf-8")
            path = root / "candidate_stdout.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            result = inspect(path, root, image_audit=False)
            self.assertIn("row_0_readiness:ready_file_binding", result["errors"])

    def test_baseline_changed_bytes_are_rejected(self):
        result = self.run_case(lambda r, p: (p / "row-000/baseline.xwd").write_bytes(b"changed"))
        self.assertIn("row_0_baseline_frame_integrity", result["errors"])

    def test_baseline_false_size_is_rejected(self):
        result = self.run_case(lambda r, p: r["rows"][0]["ready"]["baseline_frame"].update(bytes=99))
        self.assertIn("row_0_baseline_frame_integrity", result["errors"])

    def test_first_frame_false_size_is_rejected(self):
        result = self.run_case(lambda r, p: r["rows"][0]["app"]["first_visual"]["frame"].update(bytes=99))
        self.assertIn("row_0_first_frame_size", result["errors"])

    def test_map_after_click_is_rejected(self):
        result = self.run_case(lambda r, p: r["rows"][0]["ready"]["map_configure_events"][0].update(monotonic_ns=90))
        self.assertIn("row_0_map_barrier_order", result["errors"])

    def test_wrong_coordinates_are_rejected(self):
        result = self.run_case(lambda r, p: r["rows"][0]["injection"].update(x=0, y=0))
        self.assertIn("row_0_coordinate_provenance", result["errors"])

    def test_exact_save_failure_is_an_observation_not_audit_failure(self):
        result = self.run_case(lambda r, p: r["rows"][0]["app"].update(saved_text="xy"))
        self.assertEqual(result["status"], "PASS_AUDIT", result["errors"])
        self.assertEqual(result["exact_save_failures"], 1)

    def test_image_processing_cannot_target_input_directory(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            raw = packet(root)
            path = root / "candidate_stdout.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "separate derived output"):
                inspect(path, root, derived_dir=root)

    def test_busy_worker_must_span_key_dispatch(self):
        def mutation(raw, root):
            raw["fixture"]["load_conditions"] = ["cpu_busy"]
            raw["schedule"][0]["load"] = "cpu_busy"
            row = raw["rows"][0]
            row["load"] = "cpu_busy"
            row["worker"] = {"pid": 3, "exit": 0, "start_ns": 1, "end_ns": 55}
            row["injection"]["last_key_sync_returned_ns"] = 110
        result = self.run_case(mutation)
        self.assertIn("row_0_worker_not_covering_key_dispatch", result["errors"])

    def test_empty_ocr_is_not_visual_success(self):
        self.assertTrue(hasattr(audit, "ocr_status"), "empty OCR gate missing")
        self.assertEqual(audit.ocr_status("", ""), "UNRESOLVED_OR_MISMATCH")
        self.assertEqual(audit.ocr_status("h", ""), "UNRESOLVED_OR_MISMATCH")
        self.assertEqual(audit.ocr_status("h", "h"), "MATCH")

    def test_raw_source_binding_must_match_frozen_inputs(self):
        self.assertIn("binding", inspect_module.signature(inspect).parameters,
                      "raw source binding gate missing")
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            raw = packet(root)
            path = root / "candidate_stdout.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            result = inspect(path, root, image_audit=False,
                binding={"freeze_sha256": "frozen", "fixture_sha256": "fixture",
                         "source_sha256": {"candidate.py": "source"}})
            self.assertIn("freeze_sha256_mismatch", result["errors"])
            self.assertIn("fixture_sha256_mismatch", result["errors"])
            self.assertIn("source_sha256_mismatch", result["errors"])


if __name__ == "__main__":
    unittest.main()
