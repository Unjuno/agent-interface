import ast
import copy
import importlib.util
import json
import os
import sys
import threading
import time
import unittest
from pathlib import Path

PR_ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
EXPERIMENTAL = PACKAGE / "experimental_source"
FIX = PACKAGE / "baseline_source"
spec = importlib.util.spec_from_file_location("candidate_tests", PACKAGE / "support/test_cancel_release.py")
candidate_tests = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = candidate_tests
spec.loader.exec_module(candidate_tests)
candidate_tests.FIX_PATH = FIX
candidate_tests.OWNER_V13_PATH = FIX / "input_owner_v13_candidate.py"
candidate_tests.BRIDGE_V2_PATH = FIX / "bridge_v2_candidate.py"

WORKTREE = Path(__file__).resolve().parents[3]

def production_release_all():
    path = WORKTREE / "research/live_control/session_v5.py"
    tree = ast.parse(path.read_text())
    backend = next(node for node in tree.body
                   if isinstance(node, ast.ClassDef) and node.name == "Backend")
    method = next(node for node in backend.body
                  if isinstance(node, ast.FunctionDef) and node.name == "release_all")
    module = ast.Module(body=[method], type_ignores=[])
    namespace = {}
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), namespace)
    return namespace["release_all"]

def load_case(variant):
    if variant == "baseline":
        candidate_tests.OWNER_V13_PATH = FIX / "input_owner_v13_candidate.py"
        candidate_tests.BRIDGE_V2_PATH = FIX / "bridge_v2_candidate.py"
    elif variant == "late-resample":
        candidate_tests.OWNER_V13_PATH = EXPERIMENTAL / "input_owner_v13_resample_candidate.py"
        candidate_tests.BRIDGE_V2_PATH = EXPERIMENTAL / "bridge_v2_deferred_receipt_candidate.py"
    else:
        raise ValueError(variant)
    return candidate_tests.load_candidate()


class LatePerKeyResample(unittest.TestCase):
    def run_schedule(self, variant, fail_retry=False):
        bridge_test, _hm, harness, _lease, _bridge, backend = load_case(variant)
        import executor_v3
        import executor_v12
        import executor_v13

        prior_lease = executor_v12.Lease

        class ObservedLease(prior_lease):
            def __init__(self, deadline):
                super().__init__(deadline)
                self.expected_focus = 42
                self.intent_token = f"intent-late-resample-{variant}"

        executor_v12.Lease = ObservedLease
        parent = bridge_test.Backend.__bases__[0]
        missing = object()
        prior_execute = parent.__dict__.get("execute", missing)
        prior_release = parent.__dict__.get("release_all", missing)
        events = []
        aggregate_entered = threading.Event()
        allow_aggregate = threading.Event()
        partial_drained = threading.Event()
        admission_seen = threading.Event()
        terminal_seen = threading.Event()
        release_errors = []
        release_threads = []
        screen = harness.d.screen()
        harness.d.screen = lambda: screen
        root = screen.root
        original_query_pointer = root.query_pointer

        def gated_query_pointer():
            aggregate_entered.set()
            if not allow_aggregate.wait(2):
                raise TimeoutError("aggregate query gate timed out")
            return original_query_pointer()

        root.query_pointer = gated_query_pointer
        original_drain = backend._drain_owner_records

        def observed_drain():
            result = original_drain()
            records = [row for row in harness.owner.records if row.get("event") == "owner_release"]
            if aggregate_entered.is_set() and records and records[0].get("verified") is False:
                partial_drained.set()
                allow_aggregate.set()
            return result

        backend._drain_owner_records = observed_drain

        def emit(row):
            events.append(copy.deepcopy(row))
            if row.get("event") == "input_admission":
                admission_seen.set()
            if row.get("event") == "terminal":
                terminal_seen.set()

        testcase = self

        def focus_invalid_program(self, _step, _cancel, _identifier, _index):
            self.raw("F8", True)
            failed_queries = {harness.d.query_i + 2}
            if fail_retry:
                failed_queries.add(harness.d.query_i + 4)
            harness.d.query_fail_on.update(failed_queries)

            def release_owner():
                try:
                    harness.owner.call("release", self.lease)
                except BaseException as exc:
                    release_errors.append(exc)

            worker = threading.Thread(target=release_owner, daemon=True)
            release_threads.append(worker)
            worker.start()
            if not aggregate_entered.wait(1):
                raise AssertionError("aggregate phase not reached")
            raise executor_v3.DecisionRequired()

        parent.execute = focus_invalid_program
        parent.release_all = production_release_all()
        backend.sequence = 1
        backend.validate = lambda _steps: None
        backend.emit = emit
        executor = executor_v13.Executor(backend, emit)
        try:
            executor.submit(f"late-resample-{variant}", [{"op": "hold"}], 1,
                            time.perf_counter_ns() + 10_000_000_000)
            testcase.assertTrue(admission_seen.wait(1), repr(events))
            testcase.assertTrue(terminal_seen.wait(1), repr(events))
            for worker in release_threads:
                worker.join(1)
                testcase.assertFalse(worker.is_alive(), "initial owner release remained blocked")
            testcase.assertTrue(partial_drained.is_set(), "execute-exit did not inspect the partial record")
            testcase.assertEqual(release_errors, [])
            record = next(row for row in harness.owner.records if row.get("event") == "owner_release")
            testcase.assertTrue(record.get("verified"), repr(record))
            testcase.assertEqual(record.get("keys_down"), [])
            ups = [row for row in events if row.get("event") == "input_release_measurement"]
            downs = [row for row in events if row.get("event") == "input_admission"]
            terminals = [row for row in events if row.get("event") == "terminal"]
            testcase.assertEqual(len(ups), 1, repr(events))
            testcase.assertEqual(len(terminals), 1)
            testcase.assertEqual(terminals[0]["status"], "needs_decision")
            testcase.assertTrue(terminals[0]["release"]["verified"])
            testcase.assertEqual(ups[0]["physical_key_measurement"]["actuation_id"],
                                 downs[0]["physical_key_measurement"]["actuation_id"])
            testcase.assertEqual(harness.d.physical, set())
            return ups[0], downs[0], events, record
        finally:
            allow_aggregate.set()
            executor.close()
            harness.close()
            if prior_execute is missing:
                delattr(parent, "execute")
            else:
                parent.execute = prior_execute
            if prior_release is missing:
                delattr(parent, "release_all")
            else:
                parent.release_all = prior_release
            executor_v12.Lease = prior_lease

    def test_exact_candidate_baseline_keeps_receipt_unconfirmed(self):
        up, down, events, record = self.run_schedule("baseline")
        self.assertEqual(up["physical_key_measurement"]["classification"],
                         "PHYSICAL_SAMPLE_UNAVAILABLE")
        self.assertIsNone(up["physical_key_measurement"]["bracket"])
        print("OBSERVATION " + json.dumps({"case": "exact_candidate_baseline",
              "record": record, "admission": down, "release": up,
              "terminal": next(row for row in events if row.get("event") == "terminal")},
              sort_keys=True, separators=(",", ":")))

    def test_late_owner_resample_and_deferred_drain_recover_bracket(self):
        up, down, events, record = self.run_schedule("late-resample")
        measurement = up["physical_key_measurement"]
        self.assertTrue(record["verified"])
        self.assertEqual(measurement["classification"], "CONFIRMED_PHYSICAL_UP")
        self.assertEqual(measurement["identity_status"], "RETIRED")
        self.assertEqual(measurement["initial_post_sample"]["available"], False)
        self.assertEqual(measurement["initial_post_sample"]["error"], "RuntimeError")
        self.assertTrue(measurement["post_sample"]["available"])
        self.assertFalse(measurement["post_sample"]["down"])
        bracket = measurement["bracket"]
        self.assertEqual(bracket["status"], "CONFIRMED_PHYSICAL_UP")
        self.assertEqual(bracket["physical_up_interval"],
                         [measurement["pre_sample"]["finished_ns"],
                          measurement["post_sample"]["finished_ns"]])
        self.assertLessEqual(measurement["pre_sample"]["finished_ns"],
                             measurement["release_request_ns"])
        self.assertLessEqual(measurement["release_request_ns"],
                             measurement["sync_return_ns"])
        self.assertLessEqual(measurement["sync_return_ns"],
                             measurement["post_sample"]["started_ns"])
        self.assertEqual(measurement["actuation_id"],
                         down["physical_key_measurement"]["actuation_id"])
        self.assertFalse(measurement["grants_input_authority"])
        self.assertFalse(bracket["grants_input_authority"])
        self.assertFalse(measurement["application_consumption_observed"])
        self.assertFalse(bracket["application_consumption_observed"])
        receipt_index = next(i for i, row in enumerate(events)
                             if row.get("event") == "input_release_measurement")
        terminal_index = next(i for i, row in enumerate(events)
                              if row.get("event") == "terminal")
        self.assertLess(receipt_index, terminal_index)
        print("OBSERVATION " + json.dumps({"case": "late_resample_treatment",
              "record": record, "admission": down, "release": up,
              "terminal": next(row for row in events if row.get("event") == "terminal")},
              sort_keys=True, separators=(",", ":")))

    def test_retry_sample_unavailable_does_not_fabricate_confirmed_up(self):
        up, down, events, record = self.run_schedule("late-resample", fail_retry=True)
        measurement = up["physical_key_measurement"]
        self.assertEqual(measurement["classification"], "PHYSICAL_SAMPLE_UNAVAILABLE")
        self.assertIsNone(measurement["bracket"])
        self.assertNotEqual(measurement["classification"], "CONFIRMED_PHYSICAL_UP")
        print("OBSERVATION " + json.dumps({"case": "late_resample_retry_unavailable",
              "record": record, "admission": down, "release": up,
              "terminal": next(row for row in events if row.get("event") == "terminal")},
              sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
