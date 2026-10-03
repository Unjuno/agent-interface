"""Corrupt copies of retained raw; never rewrite original evidence."""
import copy
import json
from pathlib import Path
import unittest
from audit import audit

ROOT = Path(__file__).resolve().parent


class AuditMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads((ROOT / 'evidence/matrix.json').read_text(encoding='utf-8'))
        cls.freeze = (ROOT / 'FREEZE.json').read_bytes()

    def test_complete_record_has_hand_counted_outcomes(self):
        result = audit(self.raw, self.freeze)
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['rows'], 432)
        self.assertEqual(result['accepted'], {'baseline': 108, 'candidate': 48})
        self.assertEqual(result['accepted_pre_begin'], {'baseline': 60, 'candidate': 0})
        self.assertIs(result['scientific_or_product_pass'], False)

    def test_twenty_directed_corruptions_are_held(self):
        mutations = [
            lambda d: d.pop('schema'),
            lambda d: d.update(rows=None),
            lambda d: d['rows'].pop(),
            lambda d: d['rows'].append(copy.deepcopy(d['rows'][0])),
            lambda d: d['rows'].__setitem__(0, None),
            lambda d: d['rows'][0].pop('accepted'),
            lambda d: d['rows'][0].update(begin_ns=True),
            lambda d: d['rows'][0].update(started_ns=0.0),
            lambda d: d['rows'][0].update(accepted=0),
            lambda d: d['rows'][0].update(manifest_matches='false'),
            lambda d: d['rows'][0].update(arm=['baseline']),
            lambda d: d['rows'][0].update(stage_after='executed'),
            lambda d: d['rows'][0].update(request_preserved=False),
            lambda d: d['rows'][0].update(exception=None),
            lambda d: d['rows'][0].update(execution_present=True),
            lambda d: d['rows'][1].update(accepted=False),
            lambda d: d.update(freeze_sha256='0' * 64),
            lambda d: d.update(source_commit='0' * 40),
            lambda d: d.update(platform=None),
            lambda d: d['rows'][0].update(extra='unobserved'),
        ]
        self.assertEqual(len(mutations), 20)
        for index, mutate in enumerate(mutations):
            with self.subTest(mutation=index):
                changed = copy.deepcopy(self.raw)
                mutate(changed)
                result = audit(changed, self.freeze)
                self.assertEqual(result['disposition'], 'HOLD')
                self.assertTrue(result['errors'])


if __name__ == '__main__':
    unittest.main()
