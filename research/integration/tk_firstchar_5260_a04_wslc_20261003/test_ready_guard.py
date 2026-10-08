import copy
import json
from pathlib import Path
import tempfile
import unittest
from ready_guard import readiness_errors


def packet(root):
    ready = {"ready_ns": 30, "geometry": {"root_id": 10, "target_id": 11},
             "baseline_frame": {"sha256": "frame"},
             "readiness": {"scheduled": 1, "focus_callbacks": 1, "finalizations": 1}}
    app = {"pid": 12, "ready_ns": 30, "geometry": ready["geometry"],
           "baseline_frame": ready["baseline_frame"], "readiness": ready["readiness"],
           "ready_snapshot": copy.deepcopy(ready)}
    row = {"ready": ready, "app": app, "app_pid": 12,
           "app_stdout": json.dumps(app) + "\n"}
    for name, value in (("ready.json", ready), ("app_result.json", app)):
        (root / name).write_text(json.dumps(value), encoding="utf-8")
    return row


class ReadyGuardTests(unittest.TestCase):
    def run_case(self, mutation=None):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            row = packet(root)
            if mutation:
                mutation(row, root)
            return readiness_errors(root, row)

    def test_literal_immutable_epoch_accepts(self):
        self.assertEqual(self.run_case(), [])

    def test_final_ready_overwrite_rejected(self):
        def mutate(row, root):
            (root / "ready.json").write_text(json.dumps({**row["ready"], "ready_ns": 31}))
        self.assertIn("ready_file_binding", self.run_case(mutate))

    def test_app_snapshot_drift_rejected(self):
        self.assertIn("app_ready_snapshot", self.run_case(
            lambda row, root: row["app"]["ready_snapshot"].update(ready_ns=31)))

    def test_missing_witness_refused(self):
        self.assertIn("single_epoch_witness", self.run_case(
            lambda row, root: row["ready"].pop("readiness")))

    def test_duplicate_callback_witness_refused(self):
        self.assertIn("single_epoch_witness", self.run_case(
            lambda row, root: row["ready"]["readiness"].update(finalizations=2)))
        self.assertIn("single_epoch_witness", self.run_case(
            lambda row, root: row["ready"]["readiness"].update(finalizations=True)))

    def test_app_ready_metadata_drift_refused(self):
        self.assertIn("app_ready_metadata", self.run_case(
            lambda row, root: row["app"].update(ready_ns=31)))
        def missing(row, root):
            row["app"].pop("ready_ns")
            row["ready"].pop("ready_ns")
        self.assertIn("app_ready_metadata", self.run_case(missing))

    def test_false_pid_and_stdout_refused(self):
        self.assertIn("app_pid_binding", self.run_case(lambda row, root: row.update(app_pid=13)))
        self.assertIn("app_stdout_binding", self.run_case(lambda row, root: row.update(app_stdout="{}")))

    def test_app_file_drift_refused(self):
        self.assertIn("app_file_binding", self.run_case(
            lambda row, root: (root / "app_result.json").write_text("{}")))


if __name__ == "__main__":
    unittest.main()
