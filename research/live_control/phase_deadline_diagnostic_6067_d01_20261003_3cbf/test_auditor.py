"""Independent literal telemetry corruption cases, not native result guesses."""
import base64
import copy
import hashlib
import unittest
import auditor

def frame():
    empty = bytes(4096)
    unavailable = {"available": False, "raw": None, "error": {"errno": 2, "message": "not collected"}}
    def snap(begin, end, periods, cpu):
        raw = f"usage_usec {cpu}\nnr_periods {periods}\nnr_throttled 0\nthrottled_usec 0\n"
        return {"begin_ns": begin, "end_ns": end, "cpu_read_begin_ns": begin+10, "cpu_read_end_ns": end-10,
            "cpu_stat_raw": raw, "cpu_stat": {"usage_usec": cpu, "nr_periods": periods, "nr_throttled": 0, "throttled_usec": 0},
            "cpu_stat_local": copy.deepcopy(unavailable), "schedstat": copy.deepcopy(unavailable),
            "schedstats_enabled": copy.deepcopy(unavailable), "process_cpu_ns": cpu*1000,
            "thread_cpu_ns": cpu*1000, "voluntary": periods, "involuntary": 0}
    return {"index": 0, "due_ns": 2_100_000_000,
            "pre": snap(1_999_999_000, 1_999_999_900, 0, 0),
            "wait": {"begin_ns": 2_000_000_000, "return_ns": 2_117_000_000, "spin_enter_ns": None,
                     "sleeps": [{"start_ns": 2_000_000_000, "return_ns": 2_117_000_000, "requested_ns": 85_000_000}]},
            "post": snap(2_117_010_000, 2_117_020_000, 2, 1000),
            "start_ns": 2_117_030_000, "native_return_ns": 2_117_040_000, "extracted_ns": 2_117_050_000,
            "pixels_b64": base64.b64encode(empty).decode(), "pixel_sha256": hashlib.sha256(empty).hexdigest(),
            "decoded": None}

class AuditorTests(unittest.TestCase):
    def test_omitted_sleep_and_malformed_optional_are_refused(self):
        for kind in ("sleep", "schedstat"):
            f = frame()
            if kind == "sleep": f["wait"]["sleeps"] = []
            else: f["post"]["schedstat"] = {"available": True, "raw": "garbage", "error": None}
            with self.subTest(kind=kind):
                with self.assertRaises(ValueError): auditor.frame_metrics(f, f["due_ns"])

    def test_late_sleep_without_leaf_throttle_is_not_declared_quota_causal(self):
        r = auditor.frame_metrics(frame(), 2_100_000_000)
        self.assertEqual(r["wait_lateness_ns"], 17_000_000)
        self.assertEqual(r["capture_lateness_ns"], 17_030_000)
        self.assertEqual(r["post_wait_overhead_ns"], 30_000)
        self.assertEqual(r["leaf_nr_throttled_delta"], 0)
        self.assertTrue(r["coarse_wake_past_deadline"])
        self.assertIsNone(r["runqueue_wait_ns_delta"])

    def test_effective_type_counter_clock_pixel_and_sleep_corruptions_are_refused(self):
        for name in ("bool", "counter", "clock", "pixels", "sleep", "decode"):
            f = frame()
            if name == "bool": f["due_ns"] = True
            elif name == "counter": f["post"]["cpu_stat"]["nr_periods"] = False
            elif name == "clock": f["start_ns"] = 2_000_000_000
            elif name == "pixels": f["pixel_sha256"] = "0"*64
            elif name == "sleep": f["wait"]["sleeps"][0]["requested_ns"] = 1
            else: f["decoded"] = {"id": 1, "color": 0xFF0000}
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    auditor.frame_metrics(f, 2_100_000_000)

    def test_json_duplicates_nonfinite_and_bool_integer_joins_are_refused(self):
        for raw in ('{"x":0,"x":0}', '{"x":NaN}'):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError): auditor.parse(raw)
        with self.assertRaises(ValueError):
            auditor.join({"index": False}, {"index": 0}, "typed")

if __name__ == "__main__":
    unittest.main()
