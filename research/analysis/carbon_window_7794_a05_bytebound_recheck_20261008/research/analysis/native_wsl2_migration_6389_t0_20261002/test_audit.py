import copy
import unittest

from audit import audit


SCHEDULE = ["wslc", "native", "native", "wslc", "wslc", "native",
            "native", "wslc", "native", "wslc", "wslc", "native"]
TESTS = [{"id": f"contract.case_{n}", "status": "passed"} for n in range(18)]
SOURCE = {"audit.py": "a" * 64, "test_audit.py": "b" * 64}


def fixture():
    freeze = {
        "schema": "native-wsl2-migration-6389-freeze-v1",
        "expected_schedule": SCHEDULE,
        "expected_test_ids": [row["id"] for row in TESTS],
        "source_sha256": SOURCE,
        "wslc_image": "python@sha256:" + "c" * 64,
        "expected_python_version": "3.12.14",
        "native_runtime_identity": "Ubuntu-24.04/WSL2",
        "min_improvement_fraction": 0.10,
    }
    runs = []
    for index, arm in enumerate(SCHEDULE):
        wslc = arm == "wslc"
        runs.append({
            "index": index,
            "arm": arm,
            "runtime_identity": freeze["wslc_image"] if wslc else "Ubuntu-24.04/WSL2",
            "python_version": "3.12.14",
            "source_sha256": copy.deepcopy(SOURCE),
            "exit_code": 0,
            "wall_ns": 1_000_000_000 if wslc else 800_000_000,
            "max_tree_rss_kib": 120_000 if wslc else 100_000,
            "host_psi_total_before": {"some": 100, "full": 20},
            "host_psi_total_after": {"some": 100, "full": 20},
            "tests": copy.deepcopy(TESTS),
        })
    return freeze, {"schema": "native-wsl2-migration-6389-raw-v1", "runs": runs}


class MigrationAuditTests(unittest.TestCase):
    def test_identical_all_pass_with_preregistered_native_speedup_is_scoped_pass(self):
        freeze, raw = fixture()
        result = audit(raw, freeze)
        self.assertEqual(result["status"], "PASS_NATIVE_MIGRATION_SCOPED")
        self.assertEqual(result["native_median_wall_ns"], 800_000_000)

    def test_changed_arm_order_is_rejected(self):
        freeze, raw = fixture()
        raw["runs"][1]["arm"] = "wslc"
        self.assertEqual(audit(raw, freeze)["status"], "HOLD_SCHEDULE_INVALID")

    def test_source_change_between_arms_is_rejected(self):
        freeze, raw = fixture()
        raw["runs"][1]["source_sha256"]["audit.py"] = "d" * 64
        self.assertEqual(audit(raw, freeze)["status"], "STOP_SOURCE_IDENTITY_MISMATCH")

    def test_any_test_output_divergence_is_failure(self):
        freeze, raw = fixture()
        raw["runs"][1]["tests"][0]["status"] = "failed"
        self.assertEqual(audit(raw, freeze)["status"], "FAIL_SEMANTIC_OUTPUT_DIVERGENCE")

    def test_memory_pressure_delta_holds_speed_comparison(self):
        freeze, raw = fixture()
        raw["runs"][0]["host_psi_total_after"]["some"] += 1
        self.assertEqual(audit(raw, freeze)["status"], "HOLD_MEMORY_PRESSURE_CONFOUNDED")

    def test_nonzero_candidate_exit_fails(self):
        freeze, raw = fixture()
        raw["runs"][0]["exit_code"] = 1
        self.assertEqual(audit(raw, freeze)["status"], "FAIL_CANDIDATE_EXIT")

    def test_speedup_below_preregistered_threshold_does_not_pass(self):
        freeze, raw = fixture()
        for run in raw["runs"]:
            if run["arm"] == "native":
                run["wall_ns"] = 950_000_000
                run["max_tree_rss_kib"] = 120_000
        self.assertEqual(audit(raw, freeze)["status"], "NO_PREREGISTERED_BENEFIT")

    def test_wrong_wslc_image_is_rejected(self):
        freeze, raw = fixture()
        raw["runs"][0]["runtime_identity"] = "python:latest"
        self.assertEqual(audit(raw, freeze)["status"], "STOP_RUNTIME_IDENTITY_MISMATCH")

    def test_python_patch_version_mismatch_stops_before_comparison(self):
        freeze, raw = fixture()
        raw["runs"][0]["python_version"] = "3.12.3"
        self.assertEqual(audit(raw, freeze)["status"], "STOP_RUNTIME_VERSION_MISMATCH")

    def test_all_runs_consistently_using_wrong_python_version_stop(self):
        freeze, raw = fixture()
        for run in raw["runs"]:
            run["python_version"] = "3.12.3"
        self.assertEqual(audit(raw, freeze)["status"], "STOP_RUNTIME_VERSION_MISMATCH")

    def test_material_native_regression_is_not_migration_pass(self):
        freeze, raw = fixture()
        for run in raw["runs"]:
            if run["arm"] == "native":
                run["wall_ns"] = 1_200_000_000
        self.assertEqual(audit(raw, freeze)["status"], "FAIL_NATIVE_REGRESSION")


if __name__ == "__main__":
    unittest.main(verbosity=2)
