"""Pre-freeze independent-review regressions; no acquired phase outcomes."""
import base64
import copy
import hashlib
import json
import struct
import unittest
from pathlib import Path
import audit
from test_audit import control

def pulse():
    spec, so, ca, li = control()
    spec = {"kind": "pulse", "phase": 1, "width_ms": 10, "offsets": [0]*4}
    epoch = so["epoch_ns"]
    so["events"] = []
    for i in range(8):
        onset = epoch + (120*i + 12)*1_000_000
        clear = onset + 10_000_000
        so["events"].append({"id": i+1, "color": 0xFF0000 if i % 2 == 0 else 0x00FF00,
            "onset_ns": onset, "due_clear_ns": clear, "draw_start_ns": onset+1000,
            "draw_end_ns": onset+2000, "clear_start_ns": clear+1000, "clear_end_ns": clear+2000})
    raw = struct.pack("<1024I", *([0]*1024))
    for f in ca["frames"]:
        f.update(decoded=None, pixels_b64=base64.b64encode(raw).decode(),
                 pixel_sha256=hashlib.sha256(raw).hexdigest())
    return spec, so, ca, li

class IntegrityTests(unittest.TestCase):
    def test_serial_pulse_baseline_and_stale_id_rejection(self):
        record = pulse()
        self.assertEqual(audit.audit_cell(*record)["misses"], 8)
        spec, so, ca, li = record
        so["events"][0]["clear_end_ns"] = so["epoch_ns"] + 900_000_000
        raw = struct.pack("<1024I", 1, *([0xFF0000]*1023))
        ca["frames"][-1].update(decoded={"id": 1, "color": 0xFF0000},
            pixels_b64=base64.b64encode(raw).decode(), pixel_sha256=hashlib.sha256(raw).hexdigest())
        with self.assertRaises(ValueError):
            audit.audit_cell(spec, so, ca, li)

    def test_source_order_and_capture_outside_window_are_refused(self):
        for mutate in ("order", "window"):
            spec, so, ca, li = pulse()
            if mutate == "order":
                so["events"][0], so["events"][1] = so["events"][1], so["events"][0]
            else:
                ca["frames"][-1]["native_return_ns"] = so["epoch_ns"] + 1_010_000_000
                ca["frames"][-1]["extracted_ns"] = so["epoch_ns"] + 1_011_000_000
            with self.subTest(mutate=mutate):
                with self.assertRaises(ValueError):
                    audit.audit_cell(spec, so, ca, li)

    def test_auditor_requires_its_own_complete_plan(self):
        original = json.loads(Path(__file__).with_name("fixture.json").read_text())
        audit.check_fixture_plan(original)
        for mutate in ("subset", "offset", "header"):
            f = copy.deepcopy(original)
            if mutate == "subset": f["cases"] = f["cases"][3:6]
            elif mutate == "offset": f["cases"][1]["offsets"] = [0]*4
            else: f["samples_per_cell"] = True
            with self.subTest(mutate=mutate):
                with self.assertRaises(ValueError):
                    audit.check_fixture_plan(f)

    def test_type_sensitive_stream_join(self):
        audit.join({"index": 0}, {"index": 0}, "test")
        for value in (False, 0.0):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    audit.join({"index": value}, {"index": 0}, "test")

    def test_strict_journal_parser(self):
        self.assertEqual(audit.parse_record('{"index":0}'), {"index": 0})
        for raw in ('{"index":0,"index":0}', '{"index":NaN}'):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    audit.parse_record(raw)

if __name__ == "__main__":
    unittest.main()
