"""Observable application effects, never a source-text mirror."""
import unittest
from fixture import Trial

class Clock:
    def __init__(self): self.now = 0
    def ns(self): return self.now
    def sleep(self, seconds): self.now += round(seconds * 1_000_000_000)

class FixtureTests(unittest.TestCase):
    def make(self, **changes):
        spec=dict(preparation_ms=4, signal_ms=3, edit_ms=8, deadline_ms=10, signal='B')
        spec.update(changes)
        clock=Clock()
        trial=Trial(spec,clock.ns,clock.sleep)
        trial.start()
        return trial,clock
    def test_only_commit_changes_effect_ledger(self):
        trial,clock=self.make()
        trial.prepare('A')
        self.assertEqual(trial.effects, [])
        trial.edit('B')
        self.assertEqual(trial.effects, [])
    def test_commit_at_deadline_is_admitted_once(self):
        trial,clock=self.make()
        trial.prepare('A')
        clock.now=10_000_000
        self.assertEqual(trial.commit(), 'committed')
        self.assertEqual(len(trial.effects),1)
        self.assertEqual(trial.commit(), 'duplicate')
        self.assertEqual(len(trial.effects),1)
    def test_one_ns_after_deadline_has_no_effect(self):
        trial,clock=self.make()
        trial.prepare('A')
        clock.now=10_000_001
        self.assertEqual(trial.commit(), 'deadline')
        self.assertEqual(trial.effects, [])
    def test_unprepared_commit_has_no_effect(self):
        trial,_=self.make()
        self.assertEqual(trial.commit(), 'unprepared')
        self.assertEqual(trial.effects, [])
    def test_future_signal_is_hidden(self):
        trial,clock=self.make()
        self.assertEqual(trial.signal(), 'PENDING')
        clock.now=3_000_000
        self.assertEqual(trial.signal(), 'B')
    def test_rejected_edit_preserves_prepared_target(self):
        trial,_=self.make()
        trial.prepare('A')
        with self.assertRaises(ValueError): trial.edit('C')
        self.assertEqual(trial.target,'A')
    def test_valid_edit_uses_observed_service_time(self):
        trial,clock=self.make(deadline_ms=20)
        trial.prepare('A')
        trial.edit('B')
        self.assertEqual(clock.now,12_000_000)
        self.assertEqual(trial.commit(),'committed')
        self.assertEqual(trial.effects[0]['target'],'B')

if __name__=='__main__': unittest.main()
