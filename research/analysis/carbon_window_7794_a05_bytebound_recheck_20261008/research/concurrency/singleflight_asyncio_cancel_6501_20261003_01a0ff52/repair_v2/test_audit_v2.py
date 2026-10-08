"""Retained-data regressions; no candidate execution or original file writes."""
import copy
import json
from pathlib import Path
import unittest

from audit_v2 import check
from mutations import mutations

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


if __name__ == '__main__':
    unittest.main(verbosity=2)
