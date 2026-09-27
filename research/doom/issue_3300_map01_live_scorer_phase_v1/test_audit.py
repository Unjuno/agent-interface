import unittest
import json
import tempfile
from pathlib import Path

import audit
import audit_async_mode as async_mode_audit
import audit_button_inventory as button_inventory_audit
import audit_empty_action_assignment as empty_action_audit
import audit_episode_start as episode_start_audit
import audit_server_state_witness as server_state_audit


def event(name, value, start):
    return {"role": "exact_scorer_predicate", "name": name, "value": value, "status": "ok", "start_ns": start, "end_ns": start + 10, "args": []}


class AuditTests(unittest.TestCase):
    def test_reconstructs_two_attempts_and_immediate_retry_gap(self):
        names = audit.EXPECTED_FIELDS
        values1 = [10, False, False, 0, 0, 35, False, 11]
        values2 = [11, False, False, 0, 0, 35, False, 11]
        trace = []
        now = 100
        for values in (values1, values2):
            for name, value in zip(names, values):
                trace.append(event(name, value, now))
                now += 30
        row = {"api_trace": trace}
        attempts = audit.independently_reconstruct_attempts(row, "exact_scorer_predicate")
        self.assertEqual(len(attempts), 2)
        self.assertFalse(attempts[0]["coherent"])
        self.assertTrue(attempts[1]["coherent"])
        self.assertEqual(attempts[1]["inner_retry_gap_ns"], 20)

    def test_phase_is_reconstructed_as_interval_not_requested_offset(self):
        attempt = {"complete": True, "tic_before": 21, "events": [event("get_episode_time", 21, 5_000_000)]}
        edges = [
            {"tic_before": 20, "tic_after": 21, "poll_tic_delta": 1, "transition_lower_ns": 4_999_700, "transition_upper_ns": 4_999_900},
            {"tic_before": 21, "tic_after": 22, "poll_tic_delta": 1, "transition_lower_ns": 5_010_000, "transition_upper_ns": 5_010_100},
        ]
        result = audit.phase_for_attempt(attempt, edges, 28_571_429)
        self.assertEqual(result["phase_lower_ns"], 100)
        self.assertEqual(result["phase_upper_ns"], 300)
        self.assertEqual(result["uncertainty_ns"], 200)
        self.assertEqual(result["period_lower_ns_from_adjacent_edges"], 10_100)

    def test_phase_is_unidentified_when_edge_bracket_overlaps_getter_start(self):
        attempt = {"complete": True, "tic_before": 21, "events": [event("get_episode_time", 21, 5_000_000)]}
        edges = [
            {"tic_before": 20, "tic_after": 21, "poll_tic_delta": 1, "transition_lower_ns": 4_999_700, "transition_upper_ns": 5_000_100},
            {"tic_before": 21, "tic_after": 22, "poll_tic_delta": 1, "transition_lower_ns": 5_010_000, "transition_upper_ns": 5_010_100},
        ]
        self.assertIsNone(audit.phase_for_attempt(attempt, edges, 28_571_429))

    def test_schedule_is_episode_disjoint_and_expected_size(self):
        count = len(audit.SCHEDULE["phase_offsets_ns"]) * len(audit.SCHEDULE["strata"]) * audit.SCHEDULE["repeats_per_stratum_offset"]
        self.assertEqual(count, audit.SCHEDULE["expected_cases"])
        self.assertEqual(len(set(audit.SCHEDULE["phase_offsets_ns"])), len(audit.SCHEDULE["phase_offsets_ns"]))
        self.assertEqual(audit.SCHEDULE["production_scorer_calls_per_sample"], 1)
        self.assertEqual(audit.SCHEDULE["production_scorer_internal_retry_max"], 3)

    def test_case_id_is_bound_to_frozen_schedule_cell(self):
        case_id = "r00-cpu_load-p03"
        expected = audit.expected_case_specs()[case_id]
        row = {"case_id": case_id, **expected}
        self.assertEqual(audit.schedule_cell_errors(row), [])
        row["stratum"] = "idle"
        row["phase_target_ns"] = audit.SCHEDULE["phase_offsets_ns"][0]
        self.assertEqual(len(audit.schedule_cell_errors(row)), 2)

    def test_incomplete_or_api_failed_attempts_are_not_scientific_incoherence(self):
        coherent_shape = {"complete": True, "api_ok": True, "coherent": False}
        valid = [dict(coherent_shape) for _ in range(3)]
        self.assertTrue(audit.all_three_attempts_complete_incoherent(valid))
        valid[-1]["complete"] = False
        self.assertFalse(audit.all_three_attempts_complete_incoherent(valid))
        valid[-1]["complete"] = True
        valid[-1]["api_ok"] = False
        self.assertFalse(audit.all_three_attempts_complete_incoherent(valid))
        self.assertTrue(audit.formal_errors_are_fatal(["case:api_attempt_error:2"]))
        self.assertTrue(audit.formal_errors_are_fatal(["case:incomplete_internal_attempt:2"]))

    def test_incomplete_phase_trace_cannot_be_accepted(self):
        row = {"phase_trace_completion_status": "STOP_PHASE_EDGE_UNOBSERVED", "scorer_calls": [], "phase_edges": []}
        self.assertFalse(audit.phase_trace_complete(row))

    def test_malformed_trace_is_reportable_without_aborting_phase_completeness(self):
        row = {
            "phase_trace_completion_status": "complete",
            "scorer_calls": [{"role": "exact_scorer_predicate"}],
            "phase_edges": [],
            "api_trace": [{"role": "exact_scorer_predicate", "name": "get_episode_time"}],
        }
        self.assertFalse(audit.phase_trace_complete(row))

    def test_phase_trace_rejects_api_error_even_when_all_getters_return(self):
        values = [10, False, False, 0, 0, 35, False, 11]
        trace = [event(name, value, 100 + index * 20) for index, (name, value) in enumerate(zip(audit.EXPECTED_FIELDS, values))]
        trace[-1]["status"] = "error"
        row = {
            "phase_trace_completion_status": "complete",
            "scorer_calls": [{"role": "exact_scorer_predicate"}],
            "api_trace": trace,
            "phase_edges": [],
        }
        self.assertFalse(audit.phase_trace_complete(row))

    def test_server_state_audit_requires_all_repetitions(self):
        self.assertEqual(server_state_audit.repetition_set_errors([], "run20"), ["run20_row_count:0!=3"])
        self.assertEqual(server_state_audit.repetition_set_errors([{"repetition": 0}, {"repetition": 1}], "run20"), ["run20_row_count:2!=3"])
        self.assertEqual(len(server_state_audit.repetition_set_errors([{"repetition": 0}, {"repetition": 0}, {"repetition": 2}], "run20")), 1)

    def test_headless_passive_probe_is_audited_as_construction_only(self):
        root = Path(__file__).parent
        report = server_state_audit.main(root)
        self.assertEqual(report["decision"], "HOLD_NO_INDEPENDENT_LIVE_TIC")
        self.assertEqual(report["errors"], [])
        rows = report["run22_headless_passive_rows"]
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["sample_count"] >= 140 for row in rows))
        self.assertTrue(all(row["tic_tuple_unique"] == [[1, 1, 1]] for row in rows))
        self.assertTrue(all(row["advancing_api_calls"] == {"advance_action": 0, "make_action": 0, "set_action": 0} for row in rows))
        self.assertFalse(report["run22_formal_allocation"])

    def test_explicit_episode_start_did_not_change_passive_tics(self):
        root = Path(__file__).parent
        report = episode_start_audit.audit(
            root / "results/construction-clock-23/raw.json",
            root / "episode_start_construction.py",
        )
        self.assertEqual(report["decision"], "HOLD_NEW_EPISODE_DID_NOT_UNLOCK_PASSIVE_TIC")
        self.assertEqual(report["errors"], [])
        self.assertEqual(len(report["rows"]), 6)
        self.assertEqual(sum(row["explicit_new_episode"] for row in report["rows"]), 3)
        self.assertTrue(all(row["tic_tuple_unique"] == [[1, 1, 1]] for row in report["rows"]))

    def test_single_empty_action_assignment_did_not_change_passive_tics(self):
        root = Path(__file__).parent
        report = empty_action_audit.audit(
            root / "results/construction-clock-27/raw.json",
            root / "empty_action_assignment_construction.py",
        )
        self.assertEqual(report["decision"], "HOLD_EMPTY_SET_ACTION_DID_NOT_UNLOCK_PASSIVE_TIC")
        self.assertEqual(report["errors"], [])
        self.assertEqual(len(report["rows"]), 6)
        self.assertEqual(sum(row["assign_empty_action"] for row in report["rows"]), 3)
        self.assertTrue(all(row["tic_tuple_unique"] == [[1, 1, 1]] for row in report["rows"]))

    def test_empty_button_inventory_did_not_change_passive_tics(self):
        root = Path(__file__).parent
        report = button_inventory_audit.audit(
            root / "results/construction-clock-28/raw.json",
            root / "button_inventory_construction.py",
        )
        self.assertEqual(report["decision"], "HOLD_BUTTON_INVENTORY_DID_NOT_UNLOCK_PASSIVE_TIC")
        self.assertEqual(report["errors"], [])
        self.assertEqual(len(report["rows"]), 6)
        self.assertEqual(sum(row["expose_buttons"] for row in report["rows"]), 3)
        self.assertTrue(all(row["tic_tuple_unique"] == [[1, 1, 1]] for row in report["rows"]))

    def test_async_player_and_spectator_both_stay_passive_tic_static(self):
        root = Path(__file__).parent
        report = async_mode_audit.audit(
            root / "results/construction-clock-29/raw.json",
            root / "async_mode_construction.py",
        )
        self.assertEqual(report["decision"], "HOLD_BOTH_ASYNC_MODES_PASSIVE_TICS_STATIC")
        self.assertEqual(report["errors"], [])
        self.assertEqual(len(report["rows"]), 6)
        self.assertEqual(sum(row["mode"] == "Mode.ASYNC_PLAYER" for row in report["rows"]), 3)
        self.assertTrue(all(len(row["tic_tuple_unique"]) == 1 for row in report["rows"]))

    def test_failure_fraction_uses_exactly_the_predicates_three_internal_attempts(self):
        self.assertTrue(audit.three_internal_attempts_all_incoherent([
            {"status": "raised", "all_inner_attempts_incoherent": True}
        ]))
        self.assertFalse(audit.three_internal_attempts_all_incoherent([
            {"status": "returned", "all_inner_attempts_incoherent": False}
        ]))

    def test_construction_audit_has_scoped_pass_and_reconstructs_raw(self):
        rows = []
        names = audit.EXPECTED_FIELDS
        values = [10, False, False, 0, 0, 35, False, 10]
        for index, stratum in enumerate(audit.SCHEDULE["strata"]):
            role = "exact_scorer_predicate"
            trace = [
                {"role": role, "name": name, "value": value, "status": "ok", "start_ns": 1020 + i * 10, "end_ns": 1021 + i * 10, "args": []}
                for i, (name, value) in enumerate(zip(names, values))
            ]
            call = {"outer_attempt": 0, "role": role, "start_ns": 1000, "end_ns": 1200, "status": "returned", "return": {"kill_count": 0, "death_count": 0, "episode_finished": False, "player_dead": False, "map_exit": False, "sample_ns": 1150}}
            rows.append({
                "case_id": f"construction-{stratum}", "sample_id": f"sample-{index}", "episode_id": f"episode-{index}", "session_id": f"session-{index}",
                "stratum": stratum, "mode": "Mode.ASYNC_SPECTATOR", "mode_readback": "Mode.ASYNC_SPECTATOR", "map": "MAP01",
                "ticrate_configured": 35, "ticrate_readback": 35, "available_buttons": [], "available_buttons_readback": [],
                "task_input": "none; empty ASYNC_SPECTATOR clock-advance calls only", "setup_status": "ok", "cleanup": {"driver_stopped": True, "probe_stopped": True, "load_stopped": True, "game_closed": True},
                "worker_errors": [], "driver_steps": [{"tic_before": 1, "tic_after": 10}], "clock_rate": {"estimated_hz": 35.0},
                "phase_target_execution_lateness_ns": 20, "phase_edges": [
                    {"tic_before": 9, "tic_after": 10, "poll_tic_delta": 1, "transition_lower_ns": 900, "transition_upper_ns": 1005},
                    {"tic_before": 10, "tic_after": 11, "poll_tic_delta": 1, "transition_lower_ns": 2000, "transition_upper_ns": 2010},
                ], "phase_trace_completion_status": "complete", "scorer_calls": [call], "api_trace": trace,
                "source_sha256": {"runner.py": "a" * 64}, "freedoom2_wad_sha256": "b" * 64, "container_image_id": "sha256:" + "c" * 64,
            })
        with tempfile.TemporaryDirectory() as temporary:
            raw = Path(temporary) / "raw.jsonl"
            raw.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            result = audit.audit_construction(raw)
        self.assertEqual(result["decision"], "PASS_CONSTRUCTION_ONLY", result["errors"])
        self.assertFalse(result["formal_allocation"])
        self.assertEqual(result["scorer_invocations_reconstructed"], 3)
        self.assertEqual(result["identified_inner_attempt_phases"], 3)
        self.assertFalse(audit.three_internal_attempts_all_incoherent([
            {"status": "raised", "all_inner_attempts_incoherent": True},
            {"status": "raised", "all_inner_attempts_incoherent": True},
            {"status": "raised", "all_inner_attempts_incoherent": True},
        ]))


if __name__ == "__main__":
    unittest.main()
