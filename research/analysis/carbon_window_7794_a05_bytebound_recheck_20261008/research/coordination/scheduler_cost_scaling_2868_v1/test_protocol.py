#!/usr/bin/env python3
"""Construction and independent-audit tests for Issue #5021."""
import copy
import hashlib
import json
import unittest

import audit
import generate_scenarios
import runner


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.schedule = generate_scenarios.build_schedule()

    def test_schedule_is_deterministic_and_complete(self):
        self.assertEqual(self.schedule, generate_scenarios.build_schedule())
        self.assertEqual([8, 32, 128, 512, 2048], self.schedule["sizes"])
        self.assertTrue(all(len(case["blocks"]) == 15 for case in self.schedule["cases"]))
        for case in self.schedule["cases"]:
            self.assertTrue(all(len(block["candidates"]) == case["size"]
                                for block in case["blocks"]))

    def test_policy_implementations_match_declared_order(self):
        candidates = self.schedule["cases"][0]["blocks"][0]["candidates"]
        expected = [row[3] for row in sorted(candidates)]
        for policy in runner.POLICIES:
            self.assertEqual(expected, runner.execute(candidates, policy))

    def test_worker_timing_fields_are_positive(self):
        row = runner.worker(self.schedule, 8, 0, "ELIGIBLE_HEAP")
        self.assertEqual(8, row["selected_count"])
        self.assertGreater(row["process_cpu_ns"], 0)
        self.assertGreater(row["wall_ns"], 0)

    def test_raw_audit_rejects_representative_mutations(self):
        freeze = {
            "allocation": "scheduler-cost-scaling-2868-v1-20260928-01",
            "freeze_parent_commit": "test-commit",
            "source_sha256": {name: "a" * 64 for name in
                              ("generate_scenarios.py", "runner.py", "audit.py", "test_protocol.py")},
        }
        schedule_bytes = (json.dumps(self.schedule, sort_keys=True, separators=(",", ":")) + "\n").encode()
        rows = []
        for size_case in self.schedule["cases"]:
            size = size_case["size"]
            for block_spec in size_case["blocks"]:
                block = block_spec["block"]
                trace = [row[3] for row in sorted(block_spec["candidates"])]
                trace_sha = hashlib.sha256(json.dumps(trace, separators=(",", ":")).encode()).hexdigest()
                for policy in audit.POLICIES:
                    result = {"schema": "scheduler-cost-worker-v1", "size": size,
                              "block": block, "policy": policy, "selected_count": size,
                              "trace": trace, "trace_sha256": trace_sha,
                              "process_cpu_ns": 400, "wall_ns": 500}
                    rows.append({"size": size, "block": block, "policy": policy,
                                 "worker_exit_code": 0, "worker_elapsed_ns_including_startup": 1000,
                                 "worker_stdout": json.dumps(result, sort_keys=True, separators=(",", ":")),
                                 "worker_stderr": "", "result": result})
        raw = {"schema": "scheduler-cost-raw-v1", "issue": 5021, "parent_issue": 2868,
               "allocation": freeze["allocation"], "freeze_parent_commit": "test-commit",
               "source_sha256": freeze["source_sha256"],
               "schedule_sha256": hashlib.sha256(schedule_bytes).hexdigest(),
               "worker_processes_expected": len(rows), "worker_processes_observed": len(rows),
               "policies": list(audit.POLICIES), "sizes": list(audit.SIZES),
               "blocks_per_size": audit.BLOCKS, "rows": rows}
        self.assertEqual([], audit.audit_doc(raw, freeze, self.schedule, schedule_bytes))
        controls = audit.corruption_controls(raw, freeze, self.schedule, schedule_bytes)
        self.assertEqual(12, len(controls))
        self.assertTrue(all(controls.values()), controls)
        mutations = [
            lambda doc: doc["rows"].pop(),
            lambda doc: doc["rows"][0].update(worker_exit_code=1),
            lambda doc: doc["rows"][0]["result"].update(trace=["wrong"]),
            lambda doc: doc.update(schedule_sha256="0" * 64),
        ]
        for mutate in mutations:
            changed = copy.deepcopy(raw)
            mutate(changed)
            self.assertTrue(audit.audit_doc(changed, freeze, self.schedule, schedule_bytes))


if __name__ == "__main__":
    unittest.main()
