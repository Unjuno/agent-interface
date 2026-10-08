"""Construction/regression tests; never part of the scored allocation."""
import copy, json, tempfile, unittest
from pathlib import Path
import experiment as exp
import audit as independent

class Contracts(unittest.TestCase):
    def fixture(self, policy='guarded_current_patch', scenario='stable'):
        t = tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup)
        root = Path(t.name)
        case = dict(id='test-case', policy=policy, scenario=scenario, rep=0)
        row = exp.one(root, case)
        return root / case['id'], case, row

    def test_all_policy_scenarios(self):
        for policy in exp.POLICIES:
            for scenario in exp.SCENARIOS:
                with self.subTest(policy=policy, scenario=scenario):
                    d, c, row = self.fixture(policy, scenario)
                    result = independent.audit_case(d, c)
                    expected = not (
                        policy == 'fixed_snapshot' and scenario in (
                            'unrelated_edit', 'unrelated_add', 'unrelated_delete', 'write_conflict')
                        or policy == 'current_patch' and scenario == 'write_conflict')
                    self.assertEqual(result['correct'], expected)

    def corrupt(self, field, value, scenario='stable'):
        d, c, row = self.fixture(scenario=scenario)
        row[field] = value; exp.dump(d / 'result.json', row)
        with self.assertRaises(AssertionError): independent.audit_case(d, c)

    def test_wrong_final_oid(self): self.corrupt('final', '0' * 40)
    def test_clock_order(self): self.corrupt('validated_ns', -1)
    def test_bool_clock(self): self.corrupt('planned_ns', True)
    def test_missing_read(self): self.corrupt('read_receipt', {})
    def test_wrong_write_precondition(self): self.corrupt('write_before', ['100644', 'blob', '0' * 40])
    def test_wrong_reason(self): self.corrupt('reason', 'applied', 'write_conflict')
    def test_false_return_code(self): self.corrupt('git_returncode', 0, 'after_validation_change')
    def test_changed_footprint(self): self.corrupt('candidate_changed_paths', ['unrelated.txt'])
    def test_reflog_corruption(self): self.corrupt('reflog', [])

    def test_no_rerun(self):
        d, c, r = self.fixture()
        with self.assertRaises(FileExistsError): exp.one(d.parent, c)

    def test_missing_case(self):
        d, c, r = self.fixture()
        with self.assertRaises(AssertionError): independent.audit(d.parent, {'cases': [c, {**c, 'id': 'missing'}]})

    def test_duplicate_case(self):
        d, c, r = self.fixture()
        with self.assertRaises(AssertionError): independent.audit(d.parent, {'cases': [c, c]})

    def test_blob_corruption(self):
        d, c, r = self.fixture()
        blob = exp.snapshot(d / 'repo.git', r['final'])['unrelated.txt'][2]
        (d / 'repo.git' / 'objects' / blob[:2] / blob[2:]).write_bytes(b'invalid object')
        with self.assertRaises(AssertionError): independent.audit_case(d, c)

    def test_mode_only_write_conflict(self):
        d, c, r = self.fixture()
        repo = d / 'repo.git'; before = exp.snapshot(repo, r['A'])
        idx = d / 'mode.index'; e = {'GIT_INDEX_FILE': str(idx)}
        exp.git(repo, 'read-tree', r['A'], extra=e)
        exp.git(repo, 'update-index', '--cacheinfo', f"100755,{before[exp.WRITE][2]},{exp.WRITE}", extra=e)
        tree = exp.git(repo, 'write-tree', extra=e).stdout.decode().strip()
        changed = exp.text(repo, 'commit-tree', tree, '-p', r['A'], '-m', 'mode mutation')
        now = exp.snapshot(repo, changed)
        self.assertEqual(now[exp.WRITE][2], before[exp.WRITE][2])
        self.assertNotEqual(now[exp.WRITE], before[exp.WRITE])

if __name__ == '__main__': unittest.main(verbosity=2)
