import json
import unittest
from adjudicate import OBSERVED_KEYS, analyze, strict_record


class EvidenceControls(unittest.TestCase):
    def setUp(self):
        self.record = {k: k != 'execution_wrong_command' for k in OBSERVED_KEYS}

    def test_original_raw_values_not_changed_and_gate_held(self):
        before = dict(self.record)
        result = analyze(self.record)
        self.assertEqual(self.record, before)
        self.assertEqual(len(result['variants']), 6)
        self.assertTrue(all(v['original_gate'] == 'HOLD_UNEVALUABLE' for v in result['variants']))

    def test_every_missing_field_rejected(self):
        for key in OBSERVED_KEYS:
            with self.subTest(key=key), self.assertRaises(ValueError):
                strict_record(json.dumps({k:v for k,v in self.record.items() if k != key}))

    def test_every_nonboolean_rejected(self):
        for key in OBSERVED_KEYS:
            for value in (None, 0, 1, 1.0, 'true'):
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    strict_record(json.dumps(dict(self.record, **{key:value})))

    def test_duplicate_extra_nonobject_rejected(self):
        for raw in ('{"effect_at_700":true,"effect_at_700":false}',
                    json.dumps(dict(self.record, effect_at_900=True)), 'null', '[]'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                strict_record(raw)

    def test_unknown_context_not_counted_as_disagreement(self):
        rows = [v for v in analyze(self.record)['variants'] if v['release_role'] == 'terminal_includes_release']
        self.assertTrue(all(len(v['unknown']) == 4 and len(v['disagreements']) == 3 for v in rows))


if __name__ == '__main__':
    unittest.main()
