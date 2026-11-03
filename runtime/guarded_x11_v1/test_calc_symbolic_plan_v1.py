import copy
import json
import tempfile
import unittest
from pathlib import Path

from runtime.guarded_x11_v1.calc_symbolic_plan_v1 import (
    PLAN_SCHEMA, validate_and_bind_calc_plan)
from runtime.guarded_x11_v1.calc_task_artifact_v1 import CalcTaskArtifact
from runtime.guarded_x11_v1.process_identity import process_generation_from_identity


def plan():
    return {
        "schema": PLAN_SCHEMA,
        "interface_id": "planner-calc-two-cell-v1",
        "predicates": ["context_ok", "blank", "cells_match"],
        "symbols": {
            "cell_entry": {"role": "entry", "identity_predicate": "context_ok",
                           "dependencies": ["context_ok"]},
            "save_control": {"role": "save", "identity_predicate": "context_ok",
                             "dependencies": ["context_ok", "cells_match"]},
        },
        "actions": {
            "populate_cells": {"operation": "enter_pair", "target_symbol": "cell_entry",
                               "expected_effect": {"cells_match": True}},
            "persist_document": {"operation": "request_save", "target_symbol": "save_control",
                                 "expected_effect": {"cells_match": True}},
        },
        "method": {
            "name": "populate-and-save", "version": "1", "initial_state": "blank_sheet",
            "max_transitions": 2, "max_runtime_ms": 9000,
            "states": {
                "blank_sheet": {"branches": [{"when": {"context_ok": True, "blank": True},
                    "outcome": "action", "action": "populate_cells",
                    "next_state": "values_entered", "reason": None}]},
                "values_entered": {"branches": [{"when": {"context_ok": True, "cells_match": True},
                    "outcome": "action", "action": "persist_document",
                    "next_state": "save_handoff", "reason": None}]},
                "save_handoff": {"branches": [{"when": {"context_ok": True},
                    "outcome": "yield", "action": None, "next_state": None,
                    "reason": "effect_unavailable"}]},
            },
        },
    }


class CalcSymbolicPlanTests(unittest.TestCase):
    def test_parent_artifact_retains_validated_plan_digest_and_immutable_copy(self):
        source = plan()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / ("1" * 32)
            root.mkdir()
            artifact = CalcTaskArtifact(root, call_id="1" * 32,
                attempt_id="plan-custody-01", task_plan=source)
            digest = artifact.task_plan_sha256
            self.assertEqual(len(digest), 64)
            source["interface_id"] = "replaced-after-prepare"
            returned = artifact.task_plan
            returned["interface_id"] = "mutated-copy"
            self.assertEqual(artifact.task_plan["interface_id"],
                             "planner-calc-two-cell-v1")
            generation = process_generation_from_identity(20, 4321, 98765)
            artifact.bind_target(process_generation=generation,
                window_generation="b" * 64, target_xid=20, target_pid=4321,
                target_start_ticks=98765)
            descriptor = artifact.descriptor
            self.assertEqual(descriptor["task_plan_sha256"], digest)

    def test_invalid_plan_is_rejected_before_artifact_reservation(self):
        candidate = plan()
        candidate["actions"]["populate_cells"]["operation"] = "run_python"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / ("2" * 32)
            root.mkdir()
            with self.assertRaises(ValueError):
                CalcTaskArtifact(root, call_id="2" * 32,
                    attempt_id="plan-custody-invalid", task_plan=candidate)
            self.assertFalse((root / "task-artifact.fods").exists())

    def test_valid_planner_plan_binds_only_current_server_aliases(self):
        source = plan()
        result = validate_and_bind_calc_plan(source,
            session_scope="fresh-scope", surface="x11-window-42",
            target_aliases={"entry": "fresh_entry", "save": "fresh_save"})
        interface = result["interface"]
        self.assertEqual(interface["session_scope"], "fresh-scope")
        self.assertEqual(interface["surface"], "x11-window-42")
        self.assertEqual(interface["symbols"]["cell_entry"]["target_reference"], "fresh_entry")
        self.assertEqual(interface["symbols"]["save_control"]["target_reference"], "fresh_save")
        self.assertEqual(result["plan_bytes"], len(json.dumps(
            source, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()))
        self.assertEqual(len(result["plan_sha256"]), 64)
        self.assertNotIn("target_aliases", result)

    def test_semantic_plan_reuse_keeps_digest_but_rebinds_each_fresh_session(self):
        retained_plan = plan()
        first = validate_and_bind_calc_plan(retained_plan,
            session_scope="native-x11:" + "1" * 32,
            surface="x11-window-41",
            target_aliases={"entry":"entry_first","save":"save_first"})
        second = validate_and_bind_calc_plan(retained_plan,
            session_scope="native-x11:" + "2" * 32,
            surface="x11-window-77",
            target_aliases={"entry":"entry_second","save":"save_second"})

        self.assertEqual(first["plan_sha256"], second["plan_sha256"])
        self.assertEqual(first["plan_bytes"], second["plan_bytes"])
        self.assertNotEqual(first["interface"], second["interface"])
        self.assertNotEqual(first["interface"]["session_scope"],
                            second["interface"]["session_scope"])
        self.assertNotEqual(first["interface"]["surface"],
                            second["interface"]["surface"])
        self.assertEqual(first["interface"]["symbols"]["cell_entry"]
                         ["target_reference"], "entry_first")
        self.assertEqual(second["interface"]["symbols"]["cell_entry"]
                         ["target_reference"], "entry_second")
        self.assertEqual(first["interface"]["symbols"]["save_control"]
                         ["target_reference"], "save_first")
        self.assertEqual(second["interface"]["symbols"]["save_control"]
                         ["target_reference"], "save_second")

    def test_runtime_opaque_scope_and_surface_ids_are_preserved(self):
        scope = "native-x11:" + "a" * 32
        surface = "x11-window-8473921"
        result = validate_and_bind_calc_plan(plan(), session_scope=scope,
            surface=surface,
            target_aliases={"entry":"fresh_entry","save":"fresh_save"})
        self.assertEqual(result["interface"]["session_scope"], scope)
        self.assertEqual(result["interface"]["surface"], surface)

    def test_invalid_plans_refuse_before_binding(self):
        attacks = []
        arbitrary_operation = plan()
        arbitrary_operation["actions"]["populate_cells"]["operation"] = "run_python"
        attacks.append(arbitrary_operation)

        raw_input = plan()
        raw_input["actions"]["populate_cells"]["steps"] = [{"op": "text", "text": "731"}]
        attacks.append(raw_input)

        save_before_match = plan()
        save_before_match["method"]["states"]["values_entered"]["branches"][0]["when"] = {
            "context_ok": True, "blank": True}
        attacks.append(save_before_match)

        graph_success = plan()
        graph_success["method"]["states"]["save_handoff"]["branches"][0]["outcome"] = "complete"
        attacks.append(graph_success)

        unhashable_predicate = plan()
        unhashable_predicate["predicates"][0] = {"not": "a predicate name"}
        attacks.append(unhashable_predicate)

        unhashable_role = plan()
        unhashable_role["symbols"]["cell_entry"]["role"] = ["entry"]
        attacks.append(unhashable_role)

        unhashable_operation = plan()
        unhashable_operation["actions"]["populate_cells"]["operation"] = ["enter_pair"]
        attacks.append(unhashable_operation)

        unhashable_initial_state = plan()
        unhashable_initial_state["method"]["initial_state"] = ["blank_sheet"]
        attacks.append(unhashable_initial_state)

        extra_state = plan()
        extra_state["method"]["states"]["unreachable"] = copy.deepcopy(
            extra_state["method"]["states"]["save_handoff"])
        attacks.append(extra_state)

        for candidate in attacks:
            with self.subTest(candidate=candidate):
                with self.assertRaises(ValueError):
                    validate_and_bind_calc_plan(candidate,
                        session_scope="fresh-scope", surface="x11-window-42",
                        target_aliases={"entry": "fresh_entry", "save": "fresh_save"})

    def test_invalid_alias_binding_and_non_json_plan_refuse(self):
        with self.assertRaises(ValueError):
            validate_and_bind_calc_plan(plan(), session_scope="fresh-scope",
                surface="x11-window-42", target_aliases={"entry": "same", "save": "same"})
        candidate = plan()
        candidate["extra"] = object()
        with self.assertRaises(ValueError):
            validate_and_bind_calc_plan(candidate, session_scope="fresh-scope",
                surface="x11-window-42", target_aliases={"entry": "fresh_entry", "save": "fresh_save"})


if __name__ == "__main__":
    unittest.main()
