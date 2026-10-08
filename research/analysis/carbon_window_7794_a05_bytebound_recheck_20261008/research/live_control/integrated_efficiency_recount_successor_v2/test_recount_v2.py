"""Mutation-focused tests for the independent v2 recount boundaries."""
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("recount_v2", HERE / "audit_recount_v2.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class RecountBoundaryTests(unittest.TestCase):
    def detail(self, expected="token-1", values=None):
        return {
            "trace": {"arm": "plain", "task_id": "task-1"},
            "submission_records": [{
                "expected_token": expected,
                "submitted_values": [expected] if values is None else values,
                "exact": True,
            }],
        }

    def history(self, expected="token-1", values=None, exact=True):
        return [{
            "task_id": "task-1",
            "expected_token": expected,
            "submitted_values": [expected] if values is None else values,
            "exact": exact,
        }]

    def test_raw_values_and_task_detail_accept_positive_control(self):
        audit.validate_submission_row(self.history()[0], self.detail(), "plain", "task-1")

    def test_stale_exact_true_cannot_override_wrong_raw_value(self):
        history = self.history(values=["wrong"], exact=True)
        with self.assertRaisesRegex(ValueError, "raw submitted values mismatch"):
            audit.validate_submission_row(history[0], self.detail(), "plain", "task-1")

    def test_history_expected_token_must_match_task_detail(self):
        history = self.history(expected="wrong")
        with self.assertRaisesRegex(ValueError, "history oracle mismatch"):
            audit.validate_submission_row(history[0], self.detail(), "plain", "task-1")

    def test_history_values_must_match_task_detail_oracle(self):
        with self.assertRaisesRegex(ValueError, "raw submitted values mismatch"):
            audit.validate_submission_row(self.history(values=["different"])[0], self.detail(),
                                          "plain", "task-1")

    def test_history_flag_must_equal_computed_raw_exactness(self):
        with self.assertRaisesRegex(ValueError, "flag/value disagreement"):
            audit.validate_submission_row(self.history(exact=False)[0], self.detail(),
                                          "plain", "task-1")

    def test_duplicate_raw_result_id_on_distinct_paths_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            one, two = Path(tmp) / "one.json", Path(tmp) / "two.json"
            payload = {"call_id": "same-id", "usage": {"input_tokens": 1}}
            one.write_text(json.dumps(payload), encoding="utf-8")
            two.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate raw result call_id"):
                audit.index_raw_calls([one, two])

    def test_input_manifest_rejects_extra_or_missing_paths(self):
        expected = {"a.json", "b.json"}
        with self.assertRaisesRegex(ValueError, "path inventory mismatch"):
            audit.validate_path_inventory(expected, ["a.json", "extra.json"], "input")

    def test_input_manifest_rejects_duplicate_paths(self):
        with self.assertRaisesRegex(ValueError, "duplicate input path"):
            audit.validate_path_inventory({"a.json"}, ["a.json", "a.json"], "input")

    def test_input_hash_mutation_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "input bytes differ"):
            audit.validate_sha256(b"tampered", "0" * 64, "fixture.json")

    def test_unrelated_checkout_is_not_descendant_of_pinned_input_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "Audit Test"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "audit@example.invalid"], check=True)
            source = repo / "source.txt"
            source.write_text("pinned tree\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "source.txt"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "pinned"], check=True)
            pinned = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
            subprocess.run(["git", "-C", str(repo), "checkout", "--orphan", "unrelated"],
                           check=True, stdout=subprocess.DEVNULL)
            source.write_text("other checkout\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "source.txt"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "unrelated"], check=True)
            head = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
            self.assertFalse(audit.is_commit_ancestor(repo, pinned, head))


if __name__ == "__main__":
    unittest.main(verbosity=2)
