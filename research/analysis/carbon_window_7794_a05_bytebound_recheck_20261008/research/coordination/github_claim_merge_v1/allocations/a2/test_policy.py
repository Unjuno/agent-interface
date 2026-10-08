"""Local deterministic controls; no HTTP, GUI or real experiment allocation."""
import copy
import itertools
import json
import unittest
from pathlib import Path
import policy as p

PLAN = json.loads(Path(__file__).with_name('plan.json').read_text())
C = PLAN['claims']


def initial(name='unit'):
    return dict(schema='claim-merge-fixture-v1', case=name, revision=0,
                claims=[], consumed_task_ids=[], fixture_only=True)


class Tests(unittest.TestCase):
    def test_independent_merge_preserves_source(self):
        first = p.propose(initial(), C['A'])['document']
        frozen = copy.deepcopy(first)
        merged = p.propose(first, C['B'])
        self.assertEqual(first, frozen)
        self.assertEqual(merged['document']['claims'], [C['A'], C['B']])
        self.assertEqual(merged['document']['revision'], 2)
        self.assertIs(merged['grants_authority'], False)

    def test_duplicate_semantics(self):
        first = p.propose(initial(), C['A'])['document']
        r = p.propose(first, C['D'])
        self.assertEqual(r['status'], 'CONFLICT')
        self.assertEqual(r['reasons'], ['semantic_successor'])

    def test_task_and_scope(self):
        first = p.propose(initial(), C['A'])['document']
        for field in ('task_id', 'scope'):
            with self.subTest(field=field):
                b = dict(C['B'], **{field: C['A'][field]})
                self.assertIn(field, p.propose(first, b)['reasons'])

    def test_consumed(self):
        old = initial(); old['consumed_task_ids'] = [C['B']['task_id']]
        self.assertEqual(p.propose(old, C['B'])['reasons'], ['consumed_task_id'])
        self.assertEqual(p.propose(old, C['A'])['document']['consumed_task_ids'], old['consumed_task_ids'])

    def test_retry_budget(self):
        for n in (1, 2, 100):
            self.assertEqual(p.propose(initial(), C['B'], n)['status'], 'STOP_CONTENDED')
        for n in (-1, True, '1'):
            self.assertEqual(p.propose(initial(), C['B'], n)['status'], 'INVALID')

    def test_invalid_fields(self):
        for field in p.FIELDS:
            b = dict(C['B']); b.pop(field)
            self.assertEqual(p.propose(initial(), b)['status'], 'INVALID')
        b = dict(C['B'], owner=' ')
        self.assertEqual(p.propose(initial(), b)['status'], 'INVALID')

    def test_invalid_register(self):
        changes = [('revision', True), ('revision', -1), ('fixture_only', False),
                   ('claims', {}), ('consumed_task_ids', ['x', 'x']), ('case', '')]
        for key, value in changes:
            old = initial(); old[key] = value
            self.assertEqual(p.propose(old, C['B'])['status'], 'INVALID')
        old = initial(); old['claims'] = [C['A'], C['D']]
        self.assertEqual(p.propose(old, C['B'])['status'], 'INVALID')

    def test_invalid_paths(self):
        for scope in ('/abs/**', 'research/synthetic/../a/**', 'research/synthetic//a/**',
                      'research/synthetic/a*/**', 'research/synthetic/./a/**'):
            self.assertEqual(p.propose(initial(), dict(C['B'], scope=scope))['status'], 'INVALID')

    def test_all_ordered_stale_interleavings(self):
        # Exhaust every legal ordering of read and PUT for each of three clients.
        events = [(c, k) for c in 'ABC' for k in ('read', 'put')]
        rows = []
        for order in itertools.permutations(events):
            if any(order.index((c, 'read')) > order.index((c, 'put')) for c in 'ABC'):
                continue
            state = initial(); snapshots = {}; admitted = []; losers = []
            for c, event in order:
                if event == 'read':
                    snapshots[c] = (p.blob(p.encode(state)), p.propose(state, C[c])['document'])
                else:
                    expected, proposed = snapshots[c]
                    if expected == p.blob(p.encode(state)):
                        state = proposed; admitted.append(c)
                    else:
                        losers.append(c)
            self.assertEqual(state['claims'], [C[c] for c in admitted])
            # Quiescent, serialized one-shot recoveries from CURRENT each time.
            for c in losers:
                recovery = p.propose(state, C[c])
                self.assertEqual(recovery['status'], 'PROPOSE')
                state = recovery['document']; admitted.append(c)
            self.assertEqual(sorted(c['task_id'] for c in state['claims']), ['SYNTHETIC-A','SYNTHETIC-B','SYNTHETIC-C'])
            rows.append(order)
        self.assertEqual(len(rows), 90)

    def test_second_race_stop(self):
        a = p.propose(initial(), C['A'])['document']
        attempted = p.propose(a, C['B'])['document']
        actual = p.propose(a, C['C'])['document']
        self.assertNotEqual(p.blob(p.encode(actual)), p.blob(p.encode(a)))
        self.assertNotEqual(actual, attempted)
        self.assertEqual(p.propose(actual, C['B'], 1)['status'], 'STOP_CONTENDED')


if __name__ == '__main__':
    unittest.main(verbosity=2)
