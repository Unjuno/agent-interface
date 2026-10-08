import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runtime_bundle import classify_run

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT.parent / "file_join_fixtures" / "valid"
POLICY = ROOT / "SOURCE_POLICY.json"
FREEZE = ROOT / "FREEZE.json"


def _sample_count(path):
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


class RuntimeBundleTests(unittest.TestCase):
    def make_bundle(self, directory, *, source_mutation=None, summary_mutation=None):
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "events.jsonl").write_bytes((FIXTURE / "events.jsonl").read_bytes())
        (directory / "scorer-samples.jsonl").write_bytes((FIXTURE / "scorer-samples.jsonl").read_bytes())
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        sources = dict(policy["sources"])
        if source_mutation is not None:
            sources[source_mutation] = "0" * 64
        (directory / "sources.json").write_text(
            json.dumps(sources, sort_keys=True) + "\n", encoding="utf-8")
        summary = {
            "schema": "map01-independent-scorer-integration-v3",
            "controller_visible": False,
            "sample_count": _sample_count(directory / "scorer-samples.jsonl"),
            "event_count": 0,
        }
        if summary_mutation:
            summary.update(summary_mutation)
        (directory / "scorer-summary.json").write_text(
            json.dumps(summary, sort_keys=True) + "\n", encoding="utf-8")
        return directory

    def test_valid_runtime_directory_preserves_classifier_result(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = self.make_bundle(Path(temp) / "runtime")
            result = classify_run(runtime, "recover-1", max_gap_ns=100, source_policy=POLICY, freeze=FREEZE)
        self.assertEqual(result["decision"], "ADMISSION_BRACKETED_PROGRESS")
        self.assertEqual(result["reason"], "bounded_independent_progress_observed_after_first_input")

    def test_changed_source_hash_fails_closed(self):
        source_name = next(iter(json.loads(POLICY.read_text())["sources"]))
        with tempfile.TemporaryDirectory() as temp:
            runtime = self.make_bundle(Path(temp) / "runtime", source_mutation=source_name)
            result = classify_run(runtime, "recover-1", max_gap_ns=100, source_policy=POLICY, freeze=FREEZE)
        self.assertEqual(result["reason"], "source_manifest_mismatch")

    def test_unexpected_source_entry_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = self.make_bundle(Path(temp) / "runtime")
            source_path = runtime / "sources.json"
            sources = json.loads(source_path.read_text())
            sources["doom/unexpected.py"] = "f" * 64
            source_path.write_text(json.dumps(sources), encoding="utf-8")
            result = classify_run(runtime, "recover-1", max_gap_ns=100, source_policy=POLICY, freeze=FREEZE)
        self.assertEqual(result["reason"], "source_manifest_mismatch")

    def test_sample_count_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = self.make_bundle(Path(temp) / "runtime", summary_mutation={"sample_count": 99})
            result = classify_run(runtime, "recover-1", max_gap_ns=100, source_policy=POLICY, freeze=FREEZE)
        self.assertEqual(result["reason"], "scorer_summary_sample_count_mismatch")

    def test_wrong_summary_schema_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = self.make_bundle(Path(temp) / "runtime", summary_mutation={"schema": "unknown"})
            result = classify_run(runtime, "recover-1", max_gap_ns=100, source_policy=POLICY, freeze=FREEZE)
        self.assertEqual(result["reason"], "invalid_scorer_summary")

    def test_controller_visible_summary_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = self.make_bundle(Path(temp) / "runtime", summary_mutation={"controller_visible": True})
            result = classify_run(runtime, "recover-1", max_gap_ns=100, source_policy=POLICY, freeze=FREEZE)
        self.assertEqual(result["reason"], "invalid_scorer_summary")

    def test_missing_metadata_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = self.make_bundle(Path(temp) / "runtime")
            (runtime / "sources.json").unlink()
            result = classify_run(runtime, "recover-1", max_gap_ns=100, source_policy=POLICY, freeze=FREEZE)
        self.assertEqual(result["reason"], "invalid_or_missing_runtime_metadata")

    def test_changed_frozen_policy_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = self.make_bundle(Path(temp) / "runtime")
            policy_copy = Path(temp) / "SOURCE_POLICY.json"
            policy_copy.write_bytes(POLICY.read_bytes() + b" ")
            result = classify_run(runtime, "recover-1", max_gap_ns=100,
                                  source_policy=policy_copy, freeze=FREEZE)
        self.assertEqual(result["reason"], "source_policy_hash_mismatch")

    def test_malformed_scorer_rows_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = self.make_bundle(Path(temp) / "runtime")
            with (runtime / "scorer-samples.jsonl").open("a", encoding="utf-8") as stream:
                stream.write("not-json\n")
            result = classify_run(runtime, "recover-1", max_gap_ns=100,
                                  source_policy=POLICY, freeze=FREEZE)
        self.assertEqual(result["reason"], "scorer_summary_sample_count_mismatch")


if __name__ == "__main__":
    unittest.main()
