"""Frozen auditor corruption controls over synthetic, explicitly non-live evidence."""
import copy
import json
import unittest
from pathlib import Path
import audit as a

PLAN = json.loads(Path(__file__).with_name('plan.json').read_text())


def synthetic():
    rows = []
    for spec in PLAN['cases']:
        name = spec['name']
        empty = dict(schema='claim-merge-fixture-v1', case=name, revision=0,
                     claims=[], consumed_task_ids=[], fixture_only=True)
        first = dict(empty, revision=1, claims=[PLAN['claims']['A']])
        read = lambda x: dict(content=a.serial(x), sha=a.identity(a.serial(x)))
        row = dict(name=name, initial_read=read(empty), recovery_read=read(first),
                   writes=[], terminal=spec['expected_terminal'], grants_real_authority=False,
                   recovery_policy_status='CONFLICT' if name=='duplicate' else 'PROPOSE',
                   recovery_reasons=['semantic_successor'] if name=='duplicate' else [])
        state = empty
        for step, success in zip(spec['steps'], spec['success']):
            source = empty if step in ('A','B_stale') else first
            who = 'A' if step=='A' else ('C' if step=='C' else spec['candidate'])
            proposed = dict(source, revision=source['revision']+1,
                            claims=source['claims']+[PLAN['claims'][who]])
            text, sha = a.serial(proposed), a.identity(a.serial(source))
            if success:
                response = dict(kind='success', commit_sha='f'*40, content_sha=a.identity(text))
                state = proposed
            else:
                response = dict(kind='error', status=409, message=PLAN['scope']+'registers/'+name+'.json does not match '+sha)
            row['writes'].append(dict(step=step, content=text, expected_sha=sha, response=response))
        row['final_read'] = read(state)
        rows.append(row)
    return rows


class AuditTests(unittest.TestCase):
    def test_synthetic_positive(self):
        self.assertEqual(a.inspect(PLAN, synthetic())['decision'], 'PASS_BOUNDED_CLAIM_MERGE_SCOPED')

    def test_corruptions(self):
        mutations = [
            lambda r: r.pop(),
            lambda r: r[0]['initial_read'].update(sha='0'*40),
            lambda r: r[0]['recovery_read'].update(content='{}\n'),
            lambda r: r[0]['writes'][2].update(content='{}\n'),
            lambda r: r[0]['writes'][2].update(expected_sha='0'*40),
            lambda r: r[0]['writes'][0]['response'].update(content_sha='0'*40),
            lambda r: r[0]['writes'][1]['response'].update(status=403),
            lambda r: r[0]['writes'][1]['response'].update(message='tool blocked'),
            lambda r: r[1]['writes'].append(copy.deepcopy(r[1]['writes'][-1])),
            lambda r: r[1].update(recovery_reasons=['scope']),
            lambda r: r[2].update(terminal='REGISTERED'),
            lambda r: r[2]['final_read'].update(sha='0'*40),
            lambda r: r[2].update(grants_real_authority=True),
        ]
        for number, mutate in enumerate(mutations):
            with self.subTest(mutation=number):
                rows = synthetic(); mutate(rows)
                with self.assertRaises(ValueError):
                    a.inspect(PLAN, rows)


if __name__ == '__main__':
    unittest.main(verbosity=2)
