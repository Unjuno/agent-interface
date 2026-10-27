import importlib.util
import unittest
import tempfile
from unittest import mock
from pathlib import Path
from test_audit_live_v3 import AuditLiveV3Tests
from test_audit_live_v4 import IdentityTests

spec = importlib.util.spec_from_file_location('audit_v5', Path(__file__).with_name('audit_live_v5.py'))
v5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v5)


class StrictTimingTests(unittest.TestCase):
    def fixture(self):
        harness = AuditLiveV3Tests()
        events, decisions, scorer = harness.valid_case(admitted=True)
        for row in events:
            if row['event'] in ('input_admission', 'input_release_transition'):
                row.update(step=1, intent_token='token-1')
        return harness, events, decisions, scorer

    def check(self, harness, events, decisions, scorer):
        return harness.run_audit(events, decisions, scorer, auditor=v5,
                                 result_name='AUDIT_V5.json')[0]

    def test_precise_pre_cancel_admission_can_pass_scoped(self):
        h, events, decisions, scorer = self.fixture()
        result = self.check(h, events, decisions, scorer)
        self.assertEqual(result['status'], 'PASS')
        self.assertFalse(result['formal_pass'])
        self.assertEqual(result['schema'], 'map01-v39-live-threat-guard-audit-v5')

    def test_missing_equal_late_or_malformed_times_fail_closed(self):
        for admission, cancel in ((None, None), (None, 100), (90, None),
                                  (100, 100), (101, 100), (True, 100), (90, [])):
            with self.subTest(admission=admission, cancel=cancel):
                h, events, decisions, scorer = self.fixture()
                a = next(row for row in events if row['event'] == 'input_admission')
                c = next(row for row in events if row['event'] == 'cancel_requested')
                if admission is None: a.pop('admitted_ns')
                else: a['admitted_ns'] = admission
                if cancel is None: c.pop('requested_ns')
                else: c['requested_ns'] = cancel
                result = self.check(h, events, decisions, scorer)
                self.assertEqual(result['status'], 'FAIL')
                self.assertFalse(result['formal_pass'])
                self.assertFalse(result['per_cancellation'][0]['admission_temporal_order_ok'])

    def test_late_log_row_with_earlier_times_can_pass_scoped(self):
        h, events, decisions, scorer = self.fixture()
        admission = events.pop(0)
        events.insert(1, admission)
        result = self.check(h, events, decisions, scorer)
        self.assertEqual(result['status'], 'PASS')
        self.assertFalse(result['formal_pass'])

    def test_existing_v5_result_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'AUDIT_V5.json'
            output.write_bytes(b'previous evidence')
            with mock.patch.object(v5, 'ROOT', root):
                with self.assertRaises(FileExistsError):
                    v5.main()
            self.assertEqual(output.read_bytes(), b'previous evidence')

    def test_no_admission_requires_no_temporal_comparison(self):
        harness = AuditLiveV3Tests()
        events, decisions, scorer = harness.valid_case(admitted=False)
        events[0].pop('requested_ns')
        result = self.check(harness, events, decisions, scorer)
        self.assertEqual(result['status'], 'PASS')
        self.assertFalse(result['formal_pass'])


class StrictIdentityTests(IdentityTests):
    def audit(self, harness, events, decisions, scorer):
        return harness.run_audit(events, decisions, scorer, auditor=v5,
                                 result_name='AUDIT_V5.json')[0]


if __name__ == '__main__':
    unittest.main()
