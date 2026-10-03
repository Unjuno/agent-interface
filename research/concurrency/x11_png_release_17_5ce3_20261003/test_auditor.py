"""Hand-derived construction records only; no X server or scientific cell."""
import copy
import unittest
from auditor import audit

def fixture():
    plan = {"cells": [], "stall_after_request_ns": 400_000_000, "checkpoint_after_request_ns": 150_000_000}
    rows = []
    for repeat in (1, 2, 3):
        for fault in (False, True):
            for policy in ("coupled", "separate"):
                item = {"id": f"r{repeat}-{policy}-{int(fault)}", "repeat": repeat, "policy": policy, "blocked": fault}
                plan["cells"].append(item)
                key = bytearray(32); key[9] = 4
                release = 510_000_000 if fault and policy == "coupled" else 105_000_000 if fault else 95_000_000
                row = {**item, "keycode": 74, "error": None, "auto_repeat_disabled": True,
                       "times": {"write_enter": 90_000_000, "cancel_request": 100_000_000,
                                 "checkpoint": 250_000_000, "write_resume": 500_000_000 if fault else 91_000_000,
                                 "write_return": 501_000_000 if fault else 92_000_000,
                                 "program_return": 520_000_000 if fault else 98_000_000},
                       "checkpoint": {"down": fault and policy == "coupled", "writer_pending": fault,
                                      "program_pending": fault},
                       "samples": [{"at_ns": 90_000_000, "keymap": key.hex(), "buttons": 0},
                                   {"at_ns": release, "keymap": bytes(32).hex(), "buttons": 0}],
                       "app_events": [{"kind": "press", "at_ns": 80_000_000, "keycode": 74},
                                      {"kind": "release", "at_ns": release, "keycode": 74}],
                       "terminal": {"keymap": bytes(32).hex(), "buttons": 0},
                       "program": {"status": "completed", "admission": "accepted",
                                   "execution": {"program_emissions": 2, "completed_ops": [0,1,2,3],
                                                 "releases": [{"verified": True, "keys_down": [], "buttons_down": []}]}},
                       "png": {"bytes": 100, "header": "89504e470d0a1a0a", "timing_ns": {"started": 81_000_000,
                               "converted": 82_000_000, "encoded": 85_000_000,
                               "written": 502_000_000 if fault else 93_000_000,
                               "hashed": 503_000_000 if fault else 94_000_000}},
                       "write_stack": ["capture", "write", "write"], "xvfb_exit": 0}
                row["checkpoint"]["sample_at_ns"] = 250_000_000
                row["samples"].append({"at_ns":250_000_000,"tag":"checkpoint","buttons":0,
                                       "keymap":key.hex() if fault and policy == "coupled" else bytes(32).hex()})
                row["samples"][0]["tag"] = "writer_entry"
                row["samples"] = sorted(row["samples"], key=lambda s:s["at_ns"])
                row["samples"].append({"at_ns":550_000_000,"tag":"terminal","buttons":0,"keymap":bytes(32).hex()})
                row["program_input"] = {"schema":"agent-interface/program-v1","program_id":item["id"],
                    "source":{"observation_seq":1,"binding_revision":0},
                    "authority":{"lease_id":"owned-6999","expires_at_ns":2_000_000_000},
                    "terminal":{"release_all_required":True},"ops":[{"op":"focus","target":"owned"},
                        {"op":"key_state","key":"F8","down":True},
                        {"op":"observe","frame":"window_client","x":0,"y":0,"w":280,"h":180},
                        {"op":"release_all"}]}
                row["source_capture"] = {"operation_index":2,"sha256":"a"*64,
                    "capture_started_ns":79_000_000,"capture_ended_ns":80_000_000}
                row["png"].update(sha256="b"*64, source_raw_sha256="a"*64,width=280,height=180)
                row["png_write_payload"] = {"bytes":100,"header":"89504e470d0a1a0a","sha256":"b"*64}
                if policy == "separate":
                    row["cleanup_response"] = {"verified":True,"keys_down":[],"buttons_down":[]}
                rows.append(row)
    return rows, plan

class SavedOracleTests(unittest.TestCase):
    def test_reconstructs_both_physical_release_policies(self):
        rows, plan = fixture()
        self.assertEqual(audit(rows, plan)["status"], "PASS_PUBLIC_X11_PNG_RELEASE_BOUNDARY_SCOPED")

    def test_duplicate_cell_is_rejected(self):
        rows, plan = fixture(); rows[1] = copy.deepcopy(rows[0])
        with self.assertRaises(ValueError): audit(rows, plan)

    def test_non_neutral_terminal_is_rejected(self):
        rows, plan = fixture(); rows[0]["terminal"]["buttons"] = 256
        with self.assertRaises(ValueError): audit(rows, plan)

    def test_false_release_receipt_is_rejected(self):
        rows, plan = fixture(); rows[0]["program"]["execution"]["releases"][0]["verified"] = False
        with self.assertRaises(ValueError): audit(rows, plan)

    def test_late_new_press_is_rejected(self):
        rows, plan = fixture(); rows[0]["app_events"].append({"kind":"press","at_ns":300_000_000,"keycode":74})
        with self.assertRaises(ValueError): audit(rows, plan)

    def test_healthy_writer_cannot_masquerade_as_blocked(self):
        rows, plan = fixture(); rows[2]["times"]["write_resume"] = 110_000_000
        with self.assertRaises(ValueError): audit(rows, plan)

    def test_discriminator_failure_is_not_pass(self):
        rows, plan = fixture(); rows[3]["checkpoint"]["down"] = True
        next(s for s in rows[3]["samples"] if s.get("tag") == "checkpoint")["keymap"] = rows[3]["samples"][0]["keymap"]
        self.assertEqual(audit(rows, plan)["status"], "HOLD_NO_PHYSICAL_RELEASE_DISCRIMINATOR")

    def test_forged_checkpoint_label_is_rejected(self):
        rows, plan = fixture(); rows[3]["checkpoint"]["down"] = True
        with self.assertRaises(ValueError): audit(rows, plan)

    def test_substituted_source_capture_is_rejected(self):
        rows, plan = fixture(); rows[0]["source_capture"]["sha256"] = "c"*64
        with self.assertRaises(ValueError): audit(rows, plan)

    def test_substituted_payload_is_rejected(self):
        rows, plan = fixture(); rows[0]["png_write_payload"]["sha256"] = "c"*64
        with self.assertRaises(ValueError): audit(rows, plan)

    def test_unexpected_program_input_is_rejected(self):
        rows, plan = fixture(); rows[0]["program_input"]["ops"][1]["key"] = "F9"
        with self.assertRaises(ValueError): audit(rows, plan)

    def test_cleanup_refusal_is_rejected(self):
        rows, plan = fixture(); rows[1]["cleanup_response"]["verified"] = False
        with self.assertRaises(ValueError): audit(rows, plan)

if __name__ == "__main__": unittest.main()
