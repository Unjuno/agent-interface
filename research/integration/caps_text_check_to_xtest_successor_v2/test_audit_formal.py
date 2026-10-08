"""Construction checks for #8328's frozen raw-record auditor."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from audit_formal import FROZEN_PLAN, FROZEN_PLAN_SHA256, audit, audit_record, mutation_controls


def record(arm: str, case_id: str = "C01") -> dict:
    value, lock = {"current": ("aB2", 0), "guard-stable": ("aB2", 0),
                   "guard-interposed": ("Ab2", 1)}[arm]
    result = {
        "kind": "formal-public-dispatch-case",
        "study_id": "caps-text-query-xtest-a02-20261008",
        "case_id": case_id,
        "repo_head": "frozen-study-snapshot",
        "arm": arm,
        "main_backend_sha256": "c4bd1c2ccda7db43a4a62efc866547f21e2d11c0d795834f1f8e1d6b32f63126",
        "before": {"lockmask": 0, "keymap": [0] * 32},
        "after": {"lockmask": lock, "keymap": [0] * 32},
        "app_after": {"value": value},
        "response": {"result": {"status": "completed", "execution": {
            "completed_ops": [0, 1, 2], "releases": [
                {"verified": True, "keys_down": [], "buttons_down": []}]}}},
        "app": {"exit": 0, "ready": {"window": 25}},
        "app_stderr": "",
        "display": ":99",
        "display_server": {"pid": 1234, "argv": ["Xvfb", ":99", "-screen", "0", "640x240x24", "-nolisten", "tcp"], "display": ":99"},
        "driver_pid": 1235,
        "runner_sha256": "runner",
        "freeze_sha256": FROZEN_PLAN_SHA256,
        "errors": [],
        "entry_events": ([{"event": "KeyPress", "ns": 20, "char": value[0], "keycode": 38},
                          {"event": "KeyPress", "ns": 21, "char": "", "keysym": "Shift_L", "keycode": 50},
                          {"event": "KeyPress", "ns": 22, "char": value[1], "keycode": 56},
                          {"event": "KeyPress", "ns": 23, "char": value[2], "keycode": 11}] +
                         [{"event": "KeyRelease", "ns": 30 + i, "keycode": k}
                          for i, k in enumerate((38, 56, 50, 11))] +
                         [{"event": "value", "value": value}, {"event": "exit", "value": value}]),
        "program": {"ops": [{"op": "focus", "target": "entry"},
                             {"op": "text", "text": "aB2"}, {"op": "release_all"}]},
        "program_id": f"formal-{case_id}-{arm}",
        "network_boundary": {"namespace_inode": 100, "pid1_namespace_inode": 101,
                             "ipv4_non_loopback_routes": [], "ipv6_non_loopback_routes": [],
                             "up_non_loopback_interfaces": []},
        "runtime_imports": json.loads((Path(__file__).resolve().parent / "SOURCE_MANIFEST.json").read_text())[
            "expected_imports"]["current" if arm == "current" else "guard"],
    }
    original_events = result["entry_events"]
    presses = [e for e in original_events if e.get("event") == "KeyPress"]
    releases = {e["keycode"]: e for e in original_events if e.get("event") == "KeyRelease"}
    result["entry_events"] = [
        presses[0], {"event": "value", "value": value[:1]}, releases[38],
        presses[1], presses[2], {"event": "value", "value": value[:2]},
        releases[56], releases[50], presses[3], {"event": "value", "value": value},
        releases[11], {"event": "exit", "value": value},
    ]
    for index, event in enumerate(result["entry_events"]):
        event["ns"] = 100 + index
    if arm.startswith("guard-"):
        result.update(predecessor_patch_sha256="86913be26400e2ac74b051df4bc9505a97fff60fc5dc652cab04caa4b4af9d65",
                      current_main_candidate_patch_sha256=FROZEN_PLAN["source_base"]["current_main_candidate_patch_sha256"],
                      barrier_patch_sha256=FROZEN_PLAN["source_base"]["fixture_instrumentation_sha256"])
    if arm == "guard-interposed":
        result["actor"] = {"pid": 1236, "exit": 0, "stderr": "", "stdout": json.dumps({
            "candidate_sample": 0, "pre_lock": 0, "accepted": 1, "post_lock": 1, "ack_ns": 10})}
    return result


class FormalAuditTest(unittest.TestCase):
    def test_rejects_unfrozen_entry_event_type(self):
        sample = record("current")
        events = sample["entry_events"]
        events.insert(2, {"event": "MapNotify", "ns": events[1]["ns"]})
        self.assertIn("Entry event type", audit_record("C01", "current", sample))

    def test_rejects_boolean_for_integer_json_evidence(self):
        samples = []
        sample = record("current")
        sample["before"]["lockmask"] = False
        samples.append((sample, "initial LockMask exact integer"))

        sample = record("current")
        sample["before"]["keymap"][0] = False
        samples.append((sample, "initial keymap exact integer bytes"))

        sample = record("current")
        sample["response"]["result"]["execution"]["completed_ops"][0] = False
        samples.append((sample, "completed operation indices exact integers"))

        sample = record("guard-interposed")
        actor = json.loads(sample["actor"]["stdout"])
        actor["accepted"] = True
        sample["actor"]["stdout"] = json.dumps(actor)
        samples.append((sample, "actor state exact integers"))

        sample = record("guard-interposed")
        actor = json.loads(sample["actor"]["stdout"])
        actor["ack_ns"] = True
        sample["actor"]["stdout"] = json.dumps(actor)
        samples.append((sample, "actor ACK timestamp exact integer"))

        for sample, message in samples:
            with self.subTest(message=message):
                self.assertIn(message, audit_record(sample["case_id"], sample["arm"], sample))

    def test_observed_v1_c01_journal_is_valid_for_v2_event_rules(self):
        raw_path = (Path(__file__).resolve().parents[1] / "caps_text_check_to_xtest_successor_v1" /
                    "formal_runs" / "run_20261008_a01" / "C01" / "probe" / "record.json")
        actual = json.loads(raw_path.read_text())
        actual["study_id"] = "caps-text-query-xtest-a02-20261008"
        actual["freeze_sha256"] = FROZEN_PLAN_SHA256
        errors = audit_record("C01", "current", actual)
        self.assertNotIn("exact Entry KeyPress sequence", errors)
        self.assertNotIn("Entry KeyRelease count", errors)

    def test_rejects_a_modifier_press_without_its_release(self):
        sample = record("current")
        sample["entry_events"] = [e for e in sample["entry_events"]
                                  if not (e.get("event") == "KeyRelease" and e.get("keycode") == 50)]
        self.assertIn("Entry KeyPress/KeyRelease keycode balance",
                      audit_record("C01", "current", sample))

    def test_rejects_value_and_exit_rows_moved_before_input(self):
        raw_path = (Path(__file__).resolve().parents[1] / "caps_text_check_to_xtest_successor_v1" /
                    "formal_runs" / "run_20261008_a01" / "C01" / "probe" / "record.json")
        sample = json.loads(raw_path.read_text())
        sample["study_id"] = "caps-text-query-xtest-a02-20261008"
        sample["freeze_sha256"] = FROZEN_PLAN_SHA256
        terminal = [e for e in sample["entry_events"] if e.get("event") in ("value", "exit")]
        sample["entry_events"] = terminal + [
            e for e in sample["entry_events"] if e.get("event") not in ("value", "exit")
        ]
        self.assertIn("Entry event chronology", audit_record("C01", "current", sample))

    def test_rejects_key_release_before_its_press_even_when_time_is_monotonic(self):
        raw_path = (Path(__file__).resolve().parents[1] / "caps_text_check_to_xtest_successor_v1" /
                    "formal_runs" / "run_20261008_a01" / "C01" / "probe" / "record.json")
        sample = json.loads(raw_path.read_text())
        sample["study_id"] = "caps-text-query-xtest-a02-20261008"
        sample["freeze_sha256"] = FROZEN_PLAN_SHA256
        events = sample["entry_events"]
        press_index = next(i for i, e in enumerate(events)
                           if e.get("event") == "KeyPress" and e.get("char") == "a")
        release_index = next(i for i, e in enumerate(events)
                             if e.get("event") == "KeyRelease" and e.get("keycode") ==
                             events[press_index].get("keycode"))
        press = events[press_index]
        release = events[release_index]
        value_index = next(i for i, e in enumerate(events)
                           if e.get("event") == "value" and e.get("value") == "a")
        value = events[value_index]
        ns = press["ns"]
        release["ns"], press["ns"], value["ns"] = ns, ns + 1, ns + 2
        events[:] = [e for i, e in enumerate(events)
                     if i not in (press_index, value_index, release_index)]
        events[press_index:press_index] = [release, press, value]
        self.assertIn("Entry per-key chronology", audit_record("C01", "current", sample))

    def test_rejects_final_value_row_before_its_character_press(self):
        raw_path = (Path(__file__).resolve().parents[1] / "caps_text_check_to_xtest_successor_v1" /
                    "formal_runs" / "run_20261008_a01" / "C01" / "probe" / "record.json")
        sample = json.loads(raw_path.read_text())
        sample["study_id"] = "caps-text-query-xtest-a02-20261008"
        sample["freeze_sha256"] = FROZEN_PLAN_SHA256
        events = sample["entry_events"]
        press_index = next(i for i, e in enumerate(events)
                           if e.get("event") == "KeyPress" and e.get("char") == "2")
        value_index = next(i for i, e in enumerate(events)
                           if e.get("event") == "value" and e.get("value") == "aB2")
        press = events[press_index]
        value = events[value_index]
        value["ns"] = press["ns"] - 1
        events.pop(value_index)
        events.insert(press_index, value)
        self.assertIn("Entry value event after character KeyPress", audit_record("C01", "current", sample))

    def test_protocol_draft_cannot_start_formal_allocation(self):
        study = Path(__file__).resolve().parent
        repo = study.parents[3]
        with tempfile.TemporaryDirectory(prefix="caps-draft-gate-") as tmp:
            out = Path(tmp) / "formal-run"
            proc = subprocess.run(
                [sys.executable, "-B", str(study / "run_formal.py"), "--repo", str(repo),
                 "--freeze-commit", "not-a-commit", "--out", str(out)],
                text=True, capture_output=True, timeout=10,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("formal status is not frozen-not-started", proc.stderr)
            self.assertFalse(out.exists())

    def test_accepts_each_frozen_arm(self):
        for arm in ("current", "guard-stable", "guard-interposed"):
            self.assertEqual(audit_record("C01", arm, record(arm, "C01")), [])

    def test_rejects_material_corruptions(self):
        base = record("current")
        bad = dict(base, main_backend_sha256="wrong")
        self.assertTrue(audit_record("C01", "current", bad))
        bad = record("current", "C01")
        bad["after"]["keymap"][0] = 1
        self.assertTrue(audit_record("C01", "current", bad))
        bad = record("guard-interposed", "I01")
        actor = json.loads(bad["actor"]["stdout"])
        actor["ack_ns"] = 100
        bad["actor"]["stdout"] = json.dumps(actor)
        self.assertTrue(audit_record("I01", "guard-interposed", bad))

    def test_rejects_wrong_current_main_candidate_patch_identity(self):
        sample = record("guard-stable", "G01")
        sample["current_main_candidate_patch_sha256"] = "wrong"
        self.assertIn("current-main candidate patch identity",
                      audit_record("G01", "guard-stable", sample))

    def test_complete_frozen_schedule_and_mutations(self):
        with tempfile.TemporaryDirectory(prefix="caps-formal-audit-") as tmp:
            root = Path(tmp)
            preflight_boundary = {"namespace_inode": 100, "pid1_namespace_inode": 101,
                                  "ipv4_non_loopback_routes": [], "ipv6_non_loopback_routes": [],
                                  "up_non_loopback_interfaces": []}
            (root / "PREFLIGHT.json").write_text(json.dumps({
                "scope": "excluded pre-allocation readiness only", "status": "PASS",
                "network_boundary": preflight_boundary, "xtest_present": True,
                "xvfb": {"exit": 0,
                         "stderr": (Path(__file__).resolve().parent / "XVFB_EXPECTED_STDERR.txt").read_text(),
                         "stderr_blocks": 1}
            }))
            for index, (case_id, arm) in enumerate((("C01", "current"), ("G01", "guard-stable"), ("I01", "guard-interposed"),
                                 ("C02", "current"), ("G02", "guard-stable"), ("I02", "guard-interposed"),
                                 ("C03", "current"), ("G03", "guard-stable"), ("I03", "guard-interposed"))):
                dest = root / case_id
                dest.mkdir()
                row = record(arm, case_id)
                row["display_server"]["pid"] += index
                row["display"] = f":{99 + index}"
                row["display_server"]["display"] = row["display"]
                row["display_server"]["argv"][1] = row["display"]
                (dest / "record.json").write_text(json.dumps(row))
                (dest / "probe.stderr").write_text("")
                (dest / "supervisor.json").write_text(json.dumps({
                    "study_id": "caps-text-query-xtest-a02-20261008",
                    "case_id": case_id, "arm": arm,
                    "probe_exit": 0, "xvfb_exit": 0,
                    "errors": [], "network_boundary": row["network_boundary"],
                    "record_display_server_pid": row["display_server"]["pid"],
                    "xvfb": {"socket_removed": True, "lock_removed": True,
                             "stderr": (Path(__file__).resolve().parent / "XVFB_EXPECTED_STDERR.txt").read_text(),
                             "stderr_blocks": 1},
                }))
            case_index = {}
            for case_id, arm in (("C01", "current"), ("G01", "guard-stable"), ("I01", "guard-interposed"),
                                 ("C02", "current"), ("G02", "guard-stable"), ("I02", "guard-interposed"),
                                 ("C03", "current"), ("G03", "guard-stable"), ("I03", "guard-interposed")):
                case_index[case_id] = {"record_sha256": hashlib.sha256((root / case_id / "record.json").read_bytes()).hexdigest(),
                                       "supervisor_sha256": hashlib.sha256((root / case_id / "supervisor.json").read_bytes()).hexdigest(),
                                       "probe_exit": 0, "xvfb_exit": 0}
            manifest_path = Path(__file__).resolve().parent / "SOURCE_MANIFEST.json"
            (root / "RAW_INDEX.json").write_text(json.dumps({
                "schema": "caps-text-query-xtest-formal-index-v1",
                "study_id": "caps-text-query-xtest-a02-20261008",
                "status": "COMPLETE", "source_freeze_commit": "frozen-study-snapshot",
                "freeze_sha256": FROZEN_PLAN_SHA256,
                "source_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                "schedule": [{"case_id": case_id, "arm": arm, "block": i // 3 + 1}
                             for i, (case_id, arm) in enumerate((
                                 ("C01", "current"), ("G01", "guard-stable"), ("I01", "guard-interposed"),
                                 ("C02", "current"), ("G02", "guard-stable"), ("I02", "guard-interposed"),
                                 ("C03", "current"), ("G03", "guard-stable"), ("I03", "guard-interposed")))],
                "cases": case_index, "case_errors": []
            }))
            errors, result = audit(root)
            self.assertEqual(errors, [])
            self.assertEqual(result["status"], "PASS")
            controls = mutation_controls(root)
            self.assertEqual(controls["status"], "PASS")
            self.assertEqual(len(controls["controls"]), 24)
            self.assertTrue(controls["controls"]["value_and_exit_before_input"]["rejected"])
            self.assertTrue(controls["controls"]["release_before_press"]["rejected"])
            self.assertTrue(controls["controls"]["final_value_before_character_press"]["rejected"])
            self.assertTrue(controls["controls"]["wrong_current_main_candidate_patch"]["rejected"])
            self.assertTrue(controls["controls"]["boolean_lockmask_and_keymap_integer_fields"]["rejected"])
            self.assertTrue(controls["controls"]["boolean_completed_operation_index"]["rejected"])
            self.assertTrue(controls["controls"]["boolean_actor_state"]["rejected"])
            self.assertTrue(controls["controls"]["boolean_actor_ack_timestamp"]["rejected"])
            self.assertTrue(controls["controls"]["unexpected_entry_event_type"]["rejected"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
