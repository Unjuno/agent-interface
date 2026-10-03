"""Retained-data regressions; no candidate execution or original file writes."""
import copy
import json
from pathlib import Path
import unittest

from audit_v3 import check
from mutations import mutations
from gate_controls import reordered_gates, serialize
import hashlib

RAW = json.loads((Path(__file__).resolve().parents[1] / 'execution/raw.json').read_bytes())


class RetainedTraceTests(unittest.TestCase):
    def test_unchanged_raw_passes(self):
        self.assertEqual(check(RAW), [])

    def test_seven_reviewer_findings_refuse(self):
        for name, raw in mutations(RAW)[:7]:
            with self.subTest(name=name):
                self.assertTrue(check(raw))

    def test_original_controls_still_refuse(self):
        for name, raw in mutations(RAW)[7:15]:
            with self.subTest(name=name):
                self.assertTrue(check(raw))

    def test_adjacent_identity_type_and_order_controls_refuse(self):
        for name, raw in mutations(RAW)[15:]:
            with self.subTest(name=name):
                self.assertTrue(check(raw))

    def test_malformed_data_refuses_without_raising(self):
        variants = [None, [], 1, {}, {'rows': None}]
        for path, value in [('rows', [None] * 48), ('rows', [{}] * 48)]:
            altered = copy.deepcopy(RAW); altered[path] = value; variants.append(altered)
        for container, field, value in [('row', 'events', [None]), ('row', 'outcomes', [None, None]),
                                        ('row', 'after_cleanup', [None])]:
            altered = copy.deepcopy(RAW); altered['rows'][0][field] = value; variants.append(altered)
        for raw in variants:
            with self.subTest(raw_type=type(raw).__name__):
                self.assertTrue(check(raw))

    def test_json_object_key_order_is_irrelevant(self):
        reordered = json.loads(json.dumps(RAW, sort_keys=True))
        self.assertEqual(check(reordered), [])


    def test_requested_detach_precedes_gate_in_all16_partial_rows(self):
        for index, altered in reordered_gates(RAW):
            with self.subTest(index=index):
                errors = check(altered)
                self.assertTrue(errors)
                self.assertTrue(any('requested waiter detach before gate' in e for e in errors))

    def test_exact_independent_row6_witness(self):
        altered = dict(reordered_gates(RAW))[6]
        self.assertEqual(hashlib.sha256(serialize(altered)).hexdigest(),
                         'f6e789430da805a5a29e9b7ba601e115a0cbaaa53c0dc78afd3c0e39fcfb7f19')

    def test_unrequested_cancelled_waiter_need_not_detach_before_gate(self):
        altered = copy.deepcopy(RAW)
        events = altered['rows'][5]['events']  # 2/cancel_first/direct; gather awaits w0 only.
        gate = next(e for e in events if e['kind'] == 'gate_open')
        events.remove(gate)
        target_detach = next(e for e in events if e['kind'] == 'waiter_detach' and e['actor'] == 'w0')
        events.insert(events.index(target_detach) + 1, gate)
        for seq, e in enumerate(events, 1):
            e['seq'] = seq
        self.assertEqual(check(altered), [])

if __name__ == '__main__':
    unittest.main(verbosity=2)
