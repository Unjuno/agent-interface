import copy
import json
from pathlib import Path
import unittest

from join import join

RAW = json.loads((Path(__file__).parent / "RAW.json").read_text())


class JoinTests(unittest.TestCase):
    def test_actual_retained_rows_join_by_full_identity_and_hold_for_effect(self):
        result = join(RAW)
        self.assertEqual(result["status"], "PASS_IDENTITY_JOIN_SCOPED; HOLD_MISSING_TASK_EFFECT")
        self.assertEqual(len(result["pairs"]), 2)
        self.assertEqual([p["identity"]["key"] for p in result["pairs"]], ["F8", "SPACE"])
        self.assertTrue(all(p["admitted_ns"] < p["owner_keyrelease_started_ns"] <= p["owner_sync_returned_ns"] < p["release_call_returned_ns"] for p in result["pairs"]))

    def test_event_permutation_does_not_change_pairs(self):
        raw = copy.deepcopy(RAW)
        raw["events"].reverse()
        self.assertEqual(join(raw)["pairs"], join(RAW)["pairs"])

    def test_missing_or_duplicate_release_holds(self):
        raw = copy.deepcopy(RAW); raw["events"] = [e for e in raw["events"] if e["event"] != "input_release_transition"]
        self.assertEqual(join(raw)["status"], "HOLD_UNMATCHED_ADMISSION_OR_RELEASE")
        raw = copy.deepcopy(RAW); up = next(e for e in raw["events"] if e["event"] == "input_release_transition"); raw["events"].append(copy.deepcopy(up))
        self.assertEqual(join(raw)["status"], "HOLD_AMBIGUOUS_IDENTITY")

    def test_duplicate_same_key_admission_is_ambiguous(self):
        raw = copy.deepcopy(RAW); down = next(e for e in raw["events"] if e["event"] == "input_admission"); raw["events"].append(copy.deepcopy(down))
        self.assertEqual(join(raw)["status"], "HOLD_AMBIGUOUS_IDENTITY")

    def test_receipt_identity_mutations_hold(self):
        for key, value in (("key", "F9"), ("owner_id", "other"), ("intent_token", "other")):
            with self.subTest(key=key):
                raw = copy.deepcopy(RAW); up = next(e for e in raw["events"] if e["event"] == "input_release_transition"); up["owner_thread_keyup_receipt"][key] = value
                self.assertEqual(join(raw)["status"], "HOLD_RECEIPT_IDENTITY_MISMATCH")

    def test_wrong_release_identity_holds(self):
        for key, value in (("key", "F9"), ("owner_id", "other"), ("intent_token", "other"), ("step", 99)):
            with self.subTest(key=key):
                raw = copy.deepcopy(RAW); up = next(e for e in raw["events"] if e["event"] == "input_release_transition"); up[key] = value
                self.assertEqual(join(raw)["status"], "HOLD_UNMATCHED_ADMISSION_OR_RELEASE")

    def test_invalid_time_order_fails_closed(self):
        raw = copy.deepcopy(RAW); up = next(e for e in raw["events"] if e["event"] == "input_release_transition"); up["owner_thread_keyup_receipt"]["owner_keyrelease_started_ns"] = up["release_call_returned_ns"] + 1
        self.assertEqual(join(raw)["status"], "FAIL_INVALID_OR_REVERSED_TIME_ORDER")

    def test_unverified_or_authoritative_receipt_holds(self):
        raw = copy.deepcopy(RAW); up = next(e for e in raw["events"] if e["event"] == "input_release_transition"); up["physical_verification_authoritative"] = True
        self.assertEqual(join(raw)["status"], "HOLD_RECEIPT_SCOPE_OR_VERIFICATION")

    def test_reordered_keyup_operation_fails(self):
        raw = copy.deepcopy(RAW)
        ups = [i for i, op in enumerate(raw['operations']) if op['op'] == 'key-up']
        raw['operations'][ups[0]], raw['operations'][ups[1]] = raw['operations'][ups[1]], raw['operations'][ups[0]]
        self.assertEqual(join(raw)['status'], 'FAIL_RELEASE_OPERATION_ORDER_MISMATCH')

    def test_inter_up_keymap_query_fails(self):
        raw = copy.deepcopy(RAW)
        ups = [i for i, op in enumerate(raw['operations']) if op['op'] == 'key-up']
        query = {'op': 'query_keymap', 'at_ns': raw['operations'][ups[0]]['at_ns'] + 1}
        raw['operations'].insert(ups[0] + 1, query)
        ups = [i for i, op in enumerate(raw['operations']) if op['op'] == 'key-up']
        raw['between_up_operations'] = raw['operations'][ups[0] + 1:ups[1]]
        self.assertEqual(join(raw)['status'], 'FAIL_INTER_UP_KEYMAP_QUERY')

    def test_no_effect_rows_are_never_inferred_from_release_receipts(self):
        raw = copy.deepcopy(RAW)
        self.assertNotIn("independent_task_effects", raw)
        self.assertIn("HOLD_MISSING_TASK_EFFECT", join(raw)["status"])


if __name__ == "__main__": unittest.main()
