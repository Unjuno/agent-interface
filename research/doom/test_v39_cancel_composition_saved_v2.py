"""Mutate copies of saved A03 evidence; never import its producer."""
import copy
import json
from pathlib import Path
import unittest

from research.doom.audit_v39_cancel_composition_saved_v2 import audit


class SavedAuditTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads((Path(__file__).parent /
            'v39_interrupt_cancel_composition_a03_20261008/candidate.json').read_text())

    def test_retained_unique_cases_reconstruct(self):
        result = audit(self.raw)
        self.assertEqual((result['cases'], result['accepted'], result['rejected']), (10, 4, 6))
        self.assertFalse(result['producer_rerun'])

    def test_copied_corruptions_are_rejected(self):
        mutations = {
            'duplicate': lambda d: d['cases'].__setitem__(-1, copy.deepcopy(d['cases'][0])),
            'unknown-case': lambda d: d['cases'][0].__setitem__('case', 'other'),
            'missing-case': lambda d: d['cases'].pop(),
            'wrong-source': lambda d: d.__setitem__('source_main', 'other'),
            'summary-status': lambda d: d['cases'][0].__setitem__('status', 'failed'),
            'summary-release': lambda d: d['cases'][0]['release'].__setitem__('verified', False),
            'summary-release-bool-as-int': lambda d: d['cases'][0]['release'].__setitem__('verified', 1),
            'event-release': lambda d: d['cases'][0]['events'][5]['release'].__setitem__('verified', False),
            'wrong-turn': lambda d: d['cases'][0]['events'][2].__setitem__('turn_id', 'turn-2'),
            'reordered-events': lambda d: d['cases'][0]['events'].reverse(),
            'extra-event': lambda d: d['cases'][0]['events'].append({'event': 'cover_cancel'}),
            'stale-answer': lambda d: d['cases'][0].__setitem__('old_answer', {'action': 'stale'}),
            'fresh-summary': lambda d: d['cases'][0]['fresh_result'].__setitem__('thread_id', 'other'),
            'fresh-summary-bool-as-int': lambda d: d['cases'][0]['fresh_result'].__setitem__('answer_eligible', 1),
            'event-release-bool-as-int': lambda d: d['cases'][0]['events'][5]['release'].__setitem__('verified', 1),
            'fresh-event': lambda d: d['cases'][0]['events'][-1].__setitem__('answer_eligible', False),
            'interrupt-condition': lambda d: d['cases'][3].__setitem__('interrupt_fails', False),
        }
        for name, mutate in mutations.items():
            with self.subTest(mutation=name):
                data = copy.deepcopy(self.raw)
                mutate(data)
                with self.assertRaises(ValueError):
                    audit(data)


if __name__ == '__main__':
    unittest.main()
