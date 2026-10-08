import copy
import json
import unittest
from pathlib import Path

from research.live_control.audit_chromium_client_single_task_v1 import (
    audit_package,
    validate_result,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


class ChromiumClientSingleTaskAuditTests(unittest.TestCase):
    def test_merged_main_package_is_audited_as_one_task_only(self):
        result = audit_package(
            REPO_ROOT / "research/integration/chromium_client_57_4d74_20261004"
        )
        self.assertEqual(result["status"], "PASS_SCOPED_TASK1_EVIDENCE_INCOMPLETE_SIX_TASK")
        self.assertEqual(result["exact_task_count"], 1)
        self.assertEqual(result["missing_tasks"], ["task-2", "task-3", "task-4", "task-5", "task-6"])
        self.assertFalse(result["full_six_success"])

    def test_rejects_promoting_task_one_to_full_six_success(self):
        root = REPO_ROOT / "research/integration/chromium_client_57_4d74_20261004/client/caller-compiled-output"
        result = json.loads((root / "result.json").read_text(encoding="utf-8"))
        history = [json.loads(row) for row in
                   (root / "client/runtime/submission-history.jsonl").read_text().splitlines()]
        mutated = copy.deepcopy(result)
        mutated["independent_evaluation"]["success"] = True
        with self.assertRaisesRegex(ValueError, "six-task oracle"):
            validate_result(mutated, history)

    def test_rejects_boolean_counts_in_six_task_oracle(self):
        root = REPO_ROOT / "research/integration/chromium_client_57_4d74_20261004/client/caller-compiled-output"
        result = json.loads((root / "result.json").read_text(encoding="utf-8"))
        history = [json.loads(row) for row in
                   (root / "client/runtime/submission-history.jsonl").read_text().splitlines()]
        mutated = copy.deepcopy(result)
        mutated["independent_evaluation"]["exact_counts"]["task-1"] = True
        with self.assertRaisesRegex(ValueError, "six-task oracle"):
            validate_result(mutated, history)

    def test_rejects_unlinked_or_unreleased_compiled_transition(self):
        root = REPO_ROOT / "research/integration/chromium_client_57_4d74_20261004/client/caller-compiled-output"
        result = json.loads((root / "result.json").read_text(encoding="utf-8"))
        history = [json.loads(row) for row in
                   (root / "client/runtime/submission-history.jsonl").read_text().splitlines()]
        mutated = copy.deepcopy(result)
        mutated["graph"]["receipt"]["transitions"][1]["release_verified"] = False
        with self.assertRaisesRegex(ValueError, "transition release"):
            validate_result(mutated, history)

    def test_rejects_disagreement_between_transition_and_durable_terminal(self):
        root = REPO_ROOT / "research/integration/chromium_client_57_4d74_20261004/client/caller-compiled-output"
        result = json.loads((root / "result.json").read_text(encoding="utf-8"))
        history = [json.loads(row) for row in
                   (root / "client/runtime/submission-history.jsonl").read_text().splitlines()]
        mutated = copy.deepcopy(result)
        terminal = next(row for row in mutated["programs"] if row["label"] == "compiled-enter")
        terminal["terminal"]["id"] = "unlinked-action"
        with self.assertRaisesRegex(ValueError, "durable terminal"):
            validate_result(mutated, history)

    def test_rejects_submission_mismatch_with_saved_exact_record(self):
        root = REPO_ROOT / "research/integration/chromium_client_57_4d74_20261004/client/caller-compiled-output"
        result = json.loads((root / "result.json").read_text(encoding="utf-8"))
        history = [json.loads(row) for row in
                   (root / "client/runtime/submission-history.jsonl").read_text().splitlines()]
        history[0]["submitted_values"] = ["wrong-token"]
        with self.assertRaisesRegex(ValueError, "submission history"):
            validate_result(result, history)

    def test_rejects_fabricated_zero_attempt_claim(self):
        root = REPO_ROOT / "research/integration/chromium_client_57_4d74_20261004/client/caller-compiled-output"
        result = json.loads((root / "result.json").read_text(encoding="utf-8"))
        history = [json.loads(row) for row in
                   (root / "client/runtime/submission-history.jsonl").read_text().splitlines()]
        mutated = copy.deepcopy(result)
        mutated["caller"]["attempt_ledger"].append({"attempt_id": "fabricated"})
        with self.assertRaisesRegex(ValueError, "attempt ledgers"):
            validate_result(mutated, history)


if __name__ == "__main__":
    unittest.main()
