import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

import gate
import raw_auditor


def valid_raw():
    return json.dumps(
        {"schema": "gpu-diagnostic-raw-v1", "complete": True, "rows": [{"case": "fixture", "value": 7}]},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


class FailClosedGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.calls = 0
        self.source_path = self.root / "frozen_source.py"
        self.source_path.write_text("frozen source\n", encoding="utf-8")
        self.source_sha = hashlib.sha256(self.source_path.read_bytes()).hexdigest()

    def candidate(self, argv, stdout_path, stderr_path):
        self.calls += 1
        Path(stdout_path).write_bytes(valid_raw())
        Path(stderr_path).write_bytes(b"")
        return 0

    def run_case(self, **changes):
        snapshot = {
            "gpu_snapshot": "0 %, 0 MiB",
            "compute_apps": None,
            "gpu_query_exit": 0,
            "apps_query_exit": 0,
            "source_expected": self.source_sha,
            "source_path": self.source_path,
            "output_dir": self.root / "out",
        }
        snapshot.update(changes)
        runner = snapshot.pop("runner", self.candidate)
        return gate.execute(**snapshot, argv=["synthetic-candidate"], runner=runner)

    def test_empty_inventory_runs_and_byte_audits_durable_raw(self):
        result = self.run_case()
        self.assertEqual(self.calls, 1)
        self.assertEqual(result.status, "PASS_CONSTRUCTION_ONLY")
        self.assertEqual(result.raw_sha256, hashlib.sha256(valid_raw()).hexdigest())
        self.assertEqual(result.audit_errors, ())

    def test_active_process_stops_before_candidate(self):
        result = self.run_case(compute_apps=["1234, python.exe, 256 MiB"])
        self.assertEqual(self.calls, 0)
        self.assertEqual(result.status, "STOP_COMPETING_PROCESS")

    def test_failed_inventory_query_stops_before_candidate(self):
        result = self.run_case(apps_query_exit=1)
        self.assertEqual(self.calls, 0)
        self.assertEqual(result.status, "STOP_INVENTORY_QUERY_FAILED")

    def test_unparseable_gpu_snapshot_stops_before_candidate(self):
        result = self.run_case(gpu_snapshot="query error")
        self.assertEqual(self.calls, 0)
        self.assertEqual(result.status, "STOP_GPU_INVENTORY_INVALID")

    def test_malformed_process_inventory_stops_before_candidate(self):
        result = self.run_case(compute_apps=[1234])
        self.assertEqual(self.calls, 0)
        self.assertEqual(result.status, "STOP_GPU_INVENTORY_INVALID")

    def test_changed_source_digest_stops_before_candidate(self):
        self.source_path.write_text("changed source\n", encoding="utf-8")
        result = self.run_case()
        self.assertEqual(self.calls, 0)
        self.assertEqual(result.status, "STOP_SOURCE_IDENTITY_MISMATCH")

    def test_missing_source_file_stops_before_candidate(self):
        result = self.run_case(source_path=self.root / "missing.py")
        self.assertEqual(self.calls, 0)
        self.assertEqual(result.status, "STOP_SOURCE_IDENTITY_MISMATCH")

    def test_nonzero_candidate_is_retained_but_not_audited(self):
        def failed(argv, stdout_path, stderr_path):
            self.calls += 1
            Path(stdout_path).write_bytes(valid_raw())
            Path(stderr_path).write_bytes(b"candidate failed")
            return 7

        result = self.run_case(runner=failed)
        self.assertEqual(self.calls, 1)
        self.assertEqual(result.status, "STOP_CANDIDATE_NONZERO")
        self.assertFalse(result.audited)

    def test_truncated_raw_is_stopped_with_no_scientific_result(self):
        def truncated(argv, stdout_path, stderr_path):
            self.calls += 1
            Path(stdout_path).write_bytes(b'{"schema":"gpu-diagnostic-raw-v1"')
            Path(stderr_path).write_bytes(b"")
            return 0

        result = self.run_case(runner=truncated)
        self.assertEqual(result.status, "STOP_RAW_INVALID")
        self.assertEqual(result.scientific_result, "NOT_EVALUATED")
        self.assertIsNone(result.raw_sha256)

    def test_missing_raw_is_stopped_and_not_audited(self):
        def silent(argv, stdout_path, stderr_path):
            self.calls += 1
            Path(stderr_path).write_bytes(b"runner emitted no artifact")
            return 0

        result = self.run_case(runner=silent)
        self.assertEqual(result.status, "STOP_RAW_MISSING")
        self.assertEqual(result.scientific_result, "NOT_EVALUATED")
        self.assertIsNone(result.raw_sha256)
        self.assertFalse(result.audited)

    def test_existing_output_path_stops_before_candidate_without_overwrite(self):
        out = self.root / "out"
        out.mkdir()
        marker = out / "keep.txt"
        marker.write_text("untouched", encoding="utf-8")
        result = self.run_case(output_dir=out)
        self.assertEqual(self.calls, 0)
        self.assertEqual(result.status, "STOP_OUTPUT_PATH_NOT_EMPTY")
        self.assertEqual(marker.read_text(encoding="utf-8"), "untouched")

    def test_successful_artifact_has_independent_receipt_audit(self):
        result = self.run_case()
        self.assertTrue(result.audited)
        self.assertEqual(result.receipt["raw_sha256"], hashlib.sha256(valid_raw()).hexdigest())

    def test_real_child_stdout_and_stderr_are_persisted_without_tool_capture(self):
        script = self.root / "synthetic_candidate.py"
        script.write_text(
            "import json, sys\n"
            "print(json.dumps({'schema':'gpu-diagnostic-raw-v1','complete':True,'rows':[{'case':'child','value':7}]}, separators=(',',':')))\n"
            "sys.stderr.buffer.write(b'diagnostic\\n')\n",
            encoding="utf-8",
        )
        source_sha = hashlib.sha256(script.read_bytes()).hexdigest()
        result = gate.execute(
            gpu_snapshot="0 %, 0 MiB",
            compute_apps=None,
            gpu_query_exit=0,
            apps_query_exit=0,
            source_expected=source_sha,
            source_path=script,
            output_dir=self.root / "child-out",
            argv=[sys.executable, str(script)],
            runner=gate.subprocess_runner,
        )
        self.assertEqual(result.status, "PASS_CONSTRUCTION_ONLY")
        self.assertEqual((self.root / "child-out" / "candidate.stderr.bin").read_bytes(), b"diagnostic\n")
        self.assertTrue((self.root / "child-out" / "auditor.stdout.json").is_file())

    def test_post_write_raw_mutation_is_rejected_by_raw_only_auditor(self):
        result = self.run_case()
        raw_path = self.root / "out" / "candidate.stdout.json"
        raw_path.write_bytes(valid_raw() + b" ")
        errors = raw_auditor.audit(raw_path, self.root / "out" / "receipt.json")
        self.assertIn("raw_digest", errors)


if __name__ == "__main__":
    unittest.main()
