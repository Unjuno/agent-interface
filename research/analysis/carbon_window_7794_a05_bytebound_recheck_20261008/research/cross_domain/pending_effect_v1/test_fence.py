import itertools
import unittest
from fence import OutcomeFence


def row(status='COMMITTED', **overrides):
    return dict(dict(schema='application-effect-receipt-v1', session='s', operation='o',
                     attempt=1, observed_ns=20, status=status), **overrides)


class FenceTests(unittest.TestCase):
    def setUp(self):
        self.f = OutcomeFence('s', 'o', 10)

    def test_release_is_not_retry(self):
        self.f.released(True, 15)
        self.assertFalse(self.f.may_retry())
        self.assertEqual(self.f.finish_observation(), 'UNKNOWN')

    def test_final_rejection_requires_release(self):
        self.f.observe(row('REJECTED_NO_EFFECT', no_effect_final=True), 25)
        self.assertFalse(self.f.may_retry())
        self.f.released(True, 25)
        self.assertTrue(self.f.may_retry())
        self.f.begin_retry(26)
        self.assertEqual(self.f.attempt, 2)
        self.assertFalse(self.f.may_retry())

    def test_commit_never_retry(self):
        self.f.released(True, 15)
        self.f.observe(row(), 25)
        self.assertFalse(self.f.may_retry())
        self.assertEqual(self.f.finish_observation(), 'COMMITTED')

    def test_late_commit_resolves_unknown(self):
        self.assertEqual(self.f.finish_observation(), 'UNKNOWN')
        self.f.observe(row(observed_ns=1000), 1001)
        self.assertEqual(self.f.finish_observation(), 'COMMITTED')

    def test_wrong_identities_do_not_unlock(self):
        for fields in ({'session':'old'}, {'operation':'old'}, {'attempt':0}):
            self.assertEqual(self.f.observe(row('REJECTED_NO_EFFECT', no_effect_final=True, **fields), 25),
                             'IGNORED_OTHER_IDENTITY')
        self.assertFalse(self.f.may_retry())
        self.assertEqual(self.f.status, 'PENDING')

    def test_old_attempt_after_retry_ignored(self):
        self.f.observe(row('REJECTED_NO_EFFECT', no_effect_final=True), 25)
        self.f.released(True, 26); self.f.begin_retry(27)
        self.f.observe(row(observed_ns=30), 31)
        self.assertEqual(self.f.status, 'PENDING')

    def test_nonfinal_rejection_blocks(self):
        for flag in (None, False, 1, 'true'):
            f = OutcomeFence('s','o',10)
            f.observe(row('REJECTED_NO_EFFECT', no_effect_final=flag), 25)
            self.assertEqual(f.status, 'INVALID_EVIDENCE')

    def test_timestamp_types_and_bounds(self):
        for timestamp in (True, 20.0, '20', -1, 9, 26):
            f = OutcomeFence('s','o',10)
            f.observe(row(observed_ns=timestamp), 25)
            self.assertEqual(f.status, 'INVALID_EVIDENCE')

    def test_regression_latches(self):
        self.f.observe(row('PENDING', observed_ns=22), 25)
        self.f.observe(row(observed_ns=21), 26)
        self.f.observe(row(observed_ns=23), 27)
        self.assertEqual(self.f.status, 'INVALID_EVIDENCE')

    def test_terminal_conflicts_fail_closed(self):
        self.f.observe(row('COMMITTED'),25)
        self.f.observe(row('REJECTED_NO_EFFECT', observed_ns=21, no_effect_final=True),26)
        self.assertEqual(self.f.status,'INVALID_EVIDENCE')

    def test_duplicate_terminal_is_idempotent(self):
        self.f.observe(row(),25); self.f.observe(row(),26)
        self.assertEqual(self.f.status,'COMMITTED')

    def test_release_false_and_bad_types(self):
        for flag in (False, None, 1, 'true'):
            with self.assertRaises(ValueError):self.f.released(flag,15)

    def test_retry_timestamp_must_be_later(self):
        self.f.observe(row('REJECTED_NO_EFFECT',no_effect_final=True),25)
        self.f.released(True,26)
        with self.assertRaises(ValueError):self.f.begin_retry(26)

    def test_constructor_bad_input(self):
        for t in (False, -1, '10', 10.0):
            with self.assertRaises(ValueError):OutcomeFence('s','o',t)
        with self.assertRaises(ValueError):OutcomeFence('', 'o',10)

    def test_schema_and_attempt_type(self):
        for overrides in ({'schema':'wrong'}, {'attempt':True}, {'session':None}):
            f=OutcomeFence('s','o',10); f.observe(row(**overrides),25)
            self.assertEqual(f.status,'INVALID_EVIDENCE')

    def test_exhaustive_three_receipt_sequences(self):
        # 6^3 schedules, including absent/foreign/malformed evidence. Not real-world rates.
        choices=('PENDING','COMMITTED','REJECTED_NO_EFFECT','FOREIGN','BAD','ABSENT')
        for seq in itertools.product(choices, repeat=3):
            f=OutcomeFence('s','o',10);f.released(True,11)
            final_no_effect_seen=False
            for n,kind in enumerate(seq,20):
                if kind=='ABSENT':continue
                state=kind if kind in choices[:3] else 'REJECTED_NO_EFFECT'
                r=row(state, observed_ns=n, no_effect_final=True)
                if kind=='FOREIGN':r['attempt']=0
                if kind=='BAD':r['observed_ns']=True
                f.observe(r,n+1)
                final_no_effect_seen |= kind=='REJECTED_NO_EFFECT'
                self.assertFalse(f.may_retry() and not final_no_effect_seen, seq)
                if f.status in ('COMMITTED','INVALID_EVIDENCE','PENDING'):
                    self.assertFalse(f.may_retry(),seq)


if __name__=='__main__':unittest.main()
