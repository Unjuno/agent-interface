import unittest

from ledger import LedgerValidationError, summarize, validate_record


def attempt(seq, attempt_id, *, status, usage_status, input_tokens=None,
            output_tokens=None, started_ns=None):
    started_ns = seq * 10 if started_ns is None else started_ns
    return {
        "seq": seq,
        "kind": "model_attempt",
        "attempt_id": attempt_id,
        "status": status,
        "started_ns": started_ns,
        "ended_ns": started_ns + 1,
        "usage": {
            "status": usage_status,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        },
    }


class TaskLedgerSummaryTests(unittest.TestCase):
    def test_failed_attempt_is_counted_in_complete_usage_totals(self):
        result = summarize([
            attempt(1, "m1", status="failed", usage_status="reported",
                    input_tokens=13, output_tokens=0),
            attempt(2, "m2", status="completed", usage_status="reported",
                    input_tokens=20, output_tokens=4),
        ])

        self.assertEqual(result["model_attempt_count"], 2)
        self.assertEqual(result["input_tokens"], 33)
        self.assertEqual(result["output_tokens"], 4)
        self.assertEqual(result["usage_status"], "complete")

    def test_missing_usage_stays_unknown_instead_of_partial_or_zero(self):
        result = summarize([
            attempt(1, "m1", status="timeout", usage_status="unavailable"),
            attempt(2, "m2", status="completed", usage_status="reported",
                    input_tokens=20, output_tokens=4),
        ])

        self.assertEqual(result["model_attempt_count"], 2)
        self.assertIsNone(result["input_tokens"])
        self.assertIsNone(result["output_tokens"])
        self.assertEqual(result["usage_status"], "incomplete")

    def test_partial_usage_stays_unknown_instead_of_summing_known_subset(self):
        result = summarize([
            attempt(1, "m1", status="completed", usage_status="partial",
                    input_tokens=20),
        ])

        self.assertIsNone(result["input_tokens"])
        self.assertIsNone(result["output_tokens"])
        self.assertEqual(result["usage_status"], "incomplete")

    def test_runtime_task_success_cannot_substitute_for_independent_score(self):
        result = summarize([{
            "seq": 1,
            "kind": "tool_call",
            "call_id": "c1",
            "model_attempt_id": None,
            "method": "interface_guarded_compiled",
            "started_ns": 10,
            "ended_ns": 11,
            "result": {"task_success": True},
        }])

        self.assertIsNone(result["task_success"])
        self.assertEqual(result["independent_score_status"], "missing")

    def test_independent_score_is_preserved_as_distinct_outcome(self):
        result = summarize([
            attempt(1, "m1", status="completed", usage_status="reported",
                    input_tokens=8, output_tokens=2),
            {
                "seq": 2,
                "kind": "task_score",
                "scorer_id": "saved-state-oracle-v1",
                "independent": True,
                "task_success": True,
                "state_sha256": "a" * 64,
                "started_ns": 20,
                "ended_ns": 21,
            },
        ])

        self.assertTrue(result["task_success"])
        self.assertEqual(result["independent_score_status"], "recorded")

    def test_terminal_score_must_follow_all_task_events(self):
        with self.assertRaises(LedgerValidationError):
            summarize([
                {"seq": 1, "kind": "task_score", "scorer_id": "oracle-v1",
                 "independent": True, "task_success": True,
                 "state_sha256": "a" * 64, "started_ns": 10, "ended_ns": 11},
                {"seq": 2, "kind": "tool_call", "call_id": "c1",
                 "model_attempt_id": None, "method": "interface_guarded_cancel",
                 "started_ns": 20, "ended_ns": 21, "result": {}},
            ])

    def test_tool_call_cannot_reference_an_unrecorded_model_attempt(self):
        with self.assertRaises(LedgerValidationError):
            summarize([{
                "seq": 1,
                "kind": "tool_call",
                "call_id": "c1",
                "model_attempt_id": "missing",
                "method": "interface_guarded_compiled",
                "started_ns": 10,
                "ended_ns": 11,
                "result": {},
            }])

    def test_record_requires_frozen_comparison_and_raw_provenance(self):
        record = {
            "schema": "agent-interface/standard-mcp-task-ledger-v1",
            "run_id": "run-01",
            "comparison": {"arm": "integrated", "block": 1,
                           "order": 1, "task_seed": "seed-01"},
            "task": {"task_id": "task-01", "fixture_sha256": "a" * 64,
                     "scorer_sha256": "b" * 64},
            "source": {"commit": "c" * 40, "route_sha256": "d" * 64},
            "environment_sha256": "e" * 64,
            "model": {"id": "model-x", "effort": "low",
                      "request_config_sha256": "f" * 64},
            "raw_refs": [{"path": "raw/events.jsonl", "sha256": "1" * 64}],
            "events": [
                attempt(1, "m1", status="completed", usage_status="reported",
                        input_tokens=8, output_tokens=2),
                {"seq": 2, "kind": "task_score", "scorer_id": "oracle-v1",
                 "independent": True, "task_success": True,
                 "state_sha256": "2" * 64, "started_ns": 20, "ended_ns": 21},
            ],
        }
        summary = validate_record(record)
        self.assertEqual(summary["model_attempt_count"], 1)
        self.assertTrue(summary["task_success"])

    def test_record_rejects_unpinned_or_escaping_raw_reference(self):
        record = {
            "schema": "agent-interface/standard-mcp-task-ledger-v1",
            "run_id": "run-01",
            "comparison": {"arm": "integrated", "block": 1,
                           "order": 1, "task_seed": "seed-01"},
            "task": {"task_id": "task-01", "fixture_sha256": "a" * 64,
                     "scorer_sha256": "b" * 64},
            "source": {"commit": "c" * 40, "route_sha256": "d" * 64},
            "environment_sha256": "e" * 64,
            "model": None,
            "raw_refs": [{"path": "../outside.json", "sha256": "1" * 64}],
            "events": [],
        }
        with self.assertRaises(LedgerValidationError):
            validate_record(record)

    def test_raw_reference_must_name_a_normalized_file_path(self):
        record = {
            "schema": "agent-interface/standard-mcp-task-ledger-v1",
            "run_id": "run-01",
            "comparison": {"arm": "baseline", "block": 1,
                           "order": 1, "task_seed": "seed-01"},
            "task": {"task_id": "task-01", "fixture_sha256": "a" * 64,
                     "scorer_sha256": "b" * 64},
            "source": {"commit": "c" * 40, "route_sha256": "d" * 64},
            "environment_sha256": "e" * 64,
            "model": None,
            "raw_refs": [{"path": ".", "sha256": "1" * 64}],
            "events": [],
        }
        with self.assertRaises(LedgerValidationError):
            validate_record(record)


if __name__ == "__main__":
    unittest.main()
