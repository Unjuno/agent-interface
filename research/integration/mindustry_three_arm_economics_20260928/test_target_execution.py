"""Host construction tests for fresh-locator-to-dispatch composition."""

import unittest
from unittest.mock import patch

from arm_coordinator import ArmCoordinator
from target_execution_v1 import DispatchStop, dispatch_task_targets
from target_receipts_v1 import (build_palette_receipt,
                                build_world_receipt)


def source(sequence, width=1280):
    return {"sequence": sequence, "pointer_binding": {
        "surface": 91, "geometry": [0, 24, width, 760]}}


def candidate():
    return {"op": "target_reference", "point_space": "source_observation_pixels",
            "points": [{"x": 150, "y": 220}, {"x": 640, "y": 410}],
            "motion_model": "surface_origin_translation",
            "confidence_basis": "visually_unambiguous"}


def slots():
    return [{"row": 0, "column": 0, "point": [150, 220]}]


class TargetExecutionTests(unittest.TestCase):
    def setUp(self):
        self.coordinator = ArmCoordinator("plain")
        self.coordinator.resolve(source(1), 1280, 760, slots(),
                                lambda _observation: candidate())
        self.observations = iter((source(2), source(3)))
        self.clock_calls = []
        self.receipt_calls = []
        self.sent = []

    def run_dispatch(self, **overrides):
        def read_clock():
            sequence = 10 + len(self.clock_calls)
            self.clock_calls.append(sequence)
            return {"sequence": sequence, "runtime_ns": 100 + sequence}

        options = {
            "coordinator": self.coordinator,
            "task_id": "A1",
            "layout": "A",
            "observe": lambda: next(self.observations),
            "read_clock": read_clock,
            "build_receipt": lambda locator, target:
                self.receipt_calls.append((locator, target)) or {"target": target},
            "submit": lambda request: self.sent.append(request) or {
                "request_id": request["id"], "terminal": True, "released": True},
        }
        options.update(overrides)
        return dispatch_task_targets(**options)

    def test_dispatches_two_targets_with_fresh_ordered_locators(self):
        compiled = []

        def compile_request(locator, clock, task_id, target, receipt):
            compiled.append((locator, clock, task_id, target, receipt))
            return {"id": f"{task_id}-{target}",
                    "expected_sequence": locator["validated_sequence"]}

        with patch("target_execution_v1.compile_receipt_target_click", compile_request):
            result = self.run_dispatch()

        self.assertEqual([row[3] for row in compiled],
                         ["palette_point", "target_point"])
        self.assertEqual([row[0]["validated_sequence"] for row in compiled], [2, 3])
        self.assertTrue(all(row[2] == "A1" for row in compiled))
        self.assertEqual(len(self.sent), 2)
        self.assertEqual([row["target"] for row in result],
                         ["palette_point", "target_point"])

    def test_composes_real_receipt_builders_and_click_compiler(self):
        observations = iter((source(2), source(3)))
        latest = {"sequence": 1}
        sent = []

        def observe():
            value = next(observations)
            latest["sequence"] = value["sequence"]
            return value

        def build(locator, target):
            dependency = [{"sequence": 1, "box": [8, 8, 24, 24]}]
            if target == "palette_point":
                return build_palette_receipt(locator,
                                             exact_dependencies=dependency)
            return build_world_receipt(locator, exact_dependencies=dependency,
                selection_baseline_sequence=1, selection_receipt_sequence=2,
                selection_box=[88, 8, 104, 24], minimum_changed_pixels=16)

        result = dispatch_task_targets(
            coordinator=self.coordinator, task_id="A1", layout="A",
            observe=observe,
            read_clock=lambda: {"sequence": latest["sequence"],
                                "runtime_ns": 100 + latest["sequence"]},
            build_receipt=build,
            submit=lambda request: sent.append(request) or {
                "request_id": request["id"], "terminal": True, "released": True})

        self.assertEqual(len(result), 2)
        self.assertEqual([row["request"]["expected_sequence"] for row in result], [2, 3])
        self.assertEqual([row["request"]["steps"][0]["op"] for row in result],
                         ["pointer_click_receipt_target"] * 2)
        self.assertEqual(len(sent), 2)

    def test_stale_second_observation_stops_before_second_dispatch(self):
        self.observations = iter((source(2), source(3, width=1216)))
        self.sent.clear()
        with patch("target_execution_v1.compile_receipt_target_click",
                   side_effect=lambda locator, clock, task_id, target, receipt:
                       {"id": target}):
            with self.assertRaisesRegex(DispatchStop, "refused before input"):
                self.run_dispatch()
        self.assertEqual(len(self.sent), 1)

    def test_ambiguous_or_unreleased_dispatch_stops_without_retry(self):
        attempts = []

        def submit(request):
            attempts.append(request)
            return {"request_id": request["id"],
                    "terminal": True, "released": False}

        with patch("target_execution_v1.compile_receipt_target_click",
                   side_effect=lambda locator, clock, task_id, target, receipt:
                       {"id": target}):
            with self.assertRaisesRegex(DispatchStop, "terminal release receipt"):
                self.run_dispatch(submit=submit)
        self.assertEqual(len(attempts), 1)
        with self.assertRaisesRegex(DispatchStop, "already consumed"):
            self.run_dispatch(submit=submit)
        self.assertEqual(len(attempts), 1)

    def test_request_receipt_must_match_id_and_be_terminal(self):
        for receipt in (
                {"request_id": "wrong", "terminal": True, "released": True},
                {"request_id": "palette_point", "terminal": False,
                 "released": True}):
            with self.subTest(receipt=receipt):
                self.setUp()
                attempts = []

                def submit(request):
                    attempts.append(request)
                    return {**receipt, "request_id": receipt["request_id"]}

                with patch("target_execution_v1.compile_receipt_target_click",
                           side_effect=lambda locator, clock, task_id, target, spec:
                               {"id": target}):
                    with self.assertRaisesRegex(DispatchStop,
                                                "terminal release receipt"):
                        self.run_dispatch(submit=submit)
                self.assertEqual(len(attempts), 1)
                with self.assertRaisesRegex(DispatchStop, "already consumed"):
                    self.run_dispatch(submit=submit)
                self.assertEqual(len(attempts), 1)

    def test_consumed_dispatch_resets_only_after_lifecycle_advance(self):
        with patch("target_execution_v1.compile_receipt_target_click",
                   side_effect=lambda locator, clock, task_id, target, receipt:
                       {"id": target}):
            self.run_dispatch()
            with self.assertRaisesRegex(DispatchStop, "already consumed"):
                self.run_dispatch()
        self.assertEqual(len(self.sent), 2)
        self.coordinator.score(True)
        self.coordinator.reset(True)
        self.coordinator.advance()
        self.assertFalse(self.coordinator.target_dispatch_started)

    def test_clock_sequence_mismatch_stops_before_submit(self):
        observations = iter((source(2),))
        latest = {"sequence": 1}
        sent = []

        def observe():
            value = next(observations)
            latest["sequence"] = value["sequence"]
            return value

        def build(locator, target):
            return build_palette_receipt(locator,
                exact_dependencies=[{"sequence": 1, "box": [8, 8, 24, 24]}])

        with self.assertRaisesRegex(DispatchStop, "socket sequence differs"):
            dispatch_task_targets(
                coordinator=self.coordinator, task_id="A1", layout="A",
                observe=observe,
                read_clock=lambda: {"sequence": latest["sequence"] + 1,
                                    "runtime_ns": 102},
                build_receipt=build,
                submit=lambda request: sent.append(request))
        self.assertEqual(sent, [])
        with self.assertRaisesRegex(DispatchStop, "already consumed"):
            self.run_dispatch()

    def test_task_mismatch_refuses_before_observation_or_dispatch(self):
        calls = []
        with self.assertRaisesRegex(DispatchStop, "current coordinated task"):
            self.run_dispatch(task_id="A2",
                              observe=lambda: calls.append("observe"),
                              submit=lambda _request: calls.append("submit"))
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
