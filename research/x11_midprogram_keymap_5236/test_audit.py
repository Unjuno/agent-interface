import copy
import unittest

from research.x11_midprogram_keymap_5236.audit import verify


def raw_fixture():
    rows = []
    for index, name in enumerate(("control_us", "jp_to_us", "us_to_jp")):
        target = {"control_us": None, "jp_to_us": "us", "us_to_jp": "jp"}[name]
        actor_receipt = None if target is None else {"target_layout": target, "started_ns": 20, "ended_ns": 30, "exit": 0}
        rows.append({
            "row": name, "status": "row_complete", "actor_argv": None if target is None else ["setxkbmap", "-layout", target],
            "actor_exit": None if target is None else 0, "actor_target": target, "actor_receipt": actor_receipt,
            "expected_effect_hex": "7b7d0a", "saved_effect_hex": "7b7d0a",
            "initial_layout": "us" if name != "us_to_jp" else "us",
            "layout_initial_exit": 0, "layout_initial_stdout": "layout: us\n",
            "layout_after_exit": 0, "layout_after_stdout": "layout: us\n" if name != "us_to_jp" else "layout: jp\n",
            "receipt": {"status": "completed", "execution": {
                "waits": [{"started_ns": 10, "ended_ns": 40}],
                "releases": [{"verified": True, "keys_down": [], "buttons_down": []}]}},
        })
    return {"rows": rows, "xvfb": {"exit": 0, "cleanup_action": "terminate", "display": ":42"}}


class AuditTests(unittest.TestCase):
    def test_exact_rows_are_scoped_no_stale_observed(self):
        self.assertEqual(verify(raw_fixture()), "NO_STALE_EFFECT_OBSERVED")

    def test_omitted_row_rejected(self):
        row = raw_fixture(); row["rows"].pop()
        with self.assertRaises(ValueError): verify(row)

    def test_swapped_direction_rejected(self):
        row = raw_fixture(); row["rows"][1], row["rows"][2] = row["rows"][2], row["rows"][1]
        with self.assertRaises(ValueError): verify(row)

    def test_wrong_expected_bytes_detected(self):
        row = raw_fixture(); row["rows"][1]["expected_effect_hex"] = "00"
        self.assertEqual(verify(row), "FAIL_STALE_MAP_EFFECT")

    def test_absent_actor_receipt_rejected(self):
        row = raw_fixture(); row["rows"][1]["actor_argv"] = None
        with self.assertRaises(ValueError): verify(row)

    def test_changed_raw_output_detected(self):
        row = raw_fixture(); row["rows"][2]["saved_effect_hex"] = "00"
        self.assertEqual(verify(row), "FAIL_STALE_MAP_EFFECT")

    def test_controls(self):
        row = raw_fixture()
        row["rows"][1]["receipt"]["status"] = "refused"
        row["rows"][1]["saved_effect_hex"] = None
        row["rows"][2]["receipt"]["status"] = "refused"
        row["rows"][2]["saved_effect_hex"] = None
        self.assertEqual(verify(row), "PASS_MIDPROGRAM_REMAP_FAIL_CLOSED")


if __name__ == "__main__":
    unittest.main()
