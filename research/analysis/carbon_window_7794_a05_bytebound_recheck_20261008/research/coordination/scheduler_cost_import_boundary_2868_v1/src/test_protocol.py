import ast
import json
from pathlib import Path
import unittest

import audit
import runner


class ImportBoundaryProtocolTests(unittest.TestCase):
    def test_heapq_is_one_module_level_import(self):
        tree = ast.parse(Path(runner.__file__).read_text(encoding="utf-8"))
        module_imports = [node for node in tree.body if isinstance(node, ast.Import)
                          and any(alias.name == "heapq" for alias in node.names)]
        all_heapq_imports = [node for node in ast.walk(tree) if isinstance(node, ast.Import)
                             and any(alias.name == "heapq" for alias in node.names)]
        self.assertEqual(len(module_imports), 1)
        self.assertEqual(len(all_heapq_imports), 1)

    def test_stable_full_trace_for_three_policies(self):
        candidates = [[-2, 100, 0, "a"], [-2, 100, 1, "b"],
                      [-1, 90, 2, "c"], [-2, 100, 3, "d"]]
        expected = ["a", "b", "d", "c"]
        for policy in runner.POLICIES:
            with self.subTest(policy=policy):
                self.assertEqual(runner.select(candidates, policy), expected)

    def test_schedule_has_frozen_dimensions_and_unique_case_ids(self):
        path = Path(__file__).resolve().parents[1] / "input" / "scenarios.json"
        schedule = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(schedule["sizes"], list(runner.SIZES))
        self.assertEqual(schedule["blocks_per_size"], runner.BLOCKS)
        keys = [(case["size"], block["block"])
                for case in schedule["cases"] for block in case["blocks"]]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(len(keys), len(runner.SIZES) * runner.BLOCKS)

    def test_heapq_is_loaded_before_any_timed_worker(self):
        self.assertIn("heapq", runner.sys.modules)
        schedule_path = Path(__file__).resolve().parents[1] / "input" / "scenarios.json"
        freeze, schedule = runner.load_contract(schedule_path)
        sample = runner.case_candidates(schedule, 8, 0)
        result = runner.worker(schedule_path, 8, 0, "ELIGIBLE_HEAP")
        self.assertTrue(result["heapq_loaded_before_timer"])
        self.assertEqual(result["selected_count"], len(sample))
        self.assertEqual(result["schedule_sha256"], freeze["schedule_sha256"])

    def test_independent_auditor_accepts_full_packet_and_rejects_controls(self):
        package = Path(__file__).resolve().parents[1]
        freeze = json.loads((Path(__file__).resolve().parent / "FREEZE.json").read_text())
        schedule = json.loads((package / "input" / "scenarios.json").read_text())
        expected = audit.expected_map(schedule)
        rows = []
        for size in runner.SIZES:
            for block in range(runner.BLOCKS):
                for policy in runner.POLICIES:
                    trace = expected[(size, block)]
                    result = {
                        "schema": "scheduler-cost-import-boundary-worker-v1",
                        "size": size,
                        "block": block,
                        "policy": policy,
                        "selected_count": size,
                        "trace": trace,
                        "trace_sha256": audit.sha(
                            json.dumps(trace, separators=(",", ":")).encode()),
                        "queue_process_cpu_ns": 500 if policy == "ELIGIBLE_HEAP" else 1000,
                        "queue_wall_ns": 700 if policy == "ELIGIBLE_HEAP" else 1200,
                        "heapq_loaded_before_timer": True,
                        "schedule_sha256": freeze["schedule_sha256"],
                    }
                    rows.append({
                        "size": size,
                        "block": block,
                        "policy": policy,
                        "worker_exit_code": 0,
                        "worker_parse_error": None,
                        "worker_stdout": json.dumps(result, sort_keys=True,
                                                    separators=(",", ":")) + "\n",
                        "worker_stderr": "",
                        "result": result,
                    })
        raw = {
            "schema": "scheduler-cost-import-boundary-raw-v1",
            "issue": 5044,
            "allocation": freeze["allocation"],
            "source_sha256": freeze["source_sha256"],
            "schedule_sha256": freeze["schedule_sha256"],
            "worker_processes_expected": 225,
            "worker_processes_observed": 225,
            "sizes": list(runner.SIZES),
            "blocks_per_size": runner.BLOCKS,
            "policies": list(runner.POLICIES),
            "rows": rows,
        }
        baseline = audit.inspect(raw, freeze, schedule)
        self.assertEqual(baseline["decision"], "PASS_HEAP_COST_CROSSOVER_SCOPED")
        self.assertEqual(baseline["errors"], [])
        controls = ("remove_row", "duplicate_row", "issue", "allocation", "source_hash",
                    "schedule_hash", "worker_exit", "missing_result", "trace", "policy",
                    "timing_boundary", "cpu", "stdout")
        for name in controls:
            with self.subTest(control=name):
                self.assertTrue(audit.inspect(audit.mutate(raw, name), freeze, schedule)["errors"])


if __name__ == "__main__":
    unittest.main()
