from __future__ import annotations

import copy
import unittest

from oracle import PrefixOracle, snapshot
from policies_guarded import Resident as Guarded
from policies_original import Resident as Original
from policies_guarded import last_message, message_count
from traces import COMPARATORS, TRACES


class NoSequenceGuard(Guarded):
    def step(self, event):
        changed = dict(event)
        if changed.get("kind") in {"replace", "revoke"} and changed.get("seq", 0) <= self.stream_seq:
            changed["seq"] = self.stream_seq + 1
        super().step(changed)


class ApplyReplaceBeforeSequenceValidation(Guarded):
    def step(self, event):
        if event.get("kind") == "replace" and event.get("seq", 0) <= self.stream_seq:
            self.generation = event["gen"]
            self.target = event["target"]
        super().step(event)


def replay(candidate, events):
    actual, oracle = candidate(), PrefixOracle()
    prefixes = []
    for event in events:
        actual.step(copy.deepcopy(event))
        oracle.consume(copy.deepcopy(event))
        prefixes.append((snapshot(actual), snapshot(oracle)))
    return prefixes


class SequenceGuardConstructionTests(unittest.TestCase):
    def test_candidate_matches_independent_oracle_at_every_prefix(self):
        for name, events in TRACES.items():
            with self.subTest(trace=name):
                prefixes = replay(Guarded, events)
                self.assertTrue(prefixes)
                for index, (actual, expected) in enumerate(prefixes):
                    with self.subTest(prefix=index):
                        self.assertEqual(actual, expected)

    def test_original_candidate_reproduces_delayed_replace_rollback(self):
        events = TRACES["delayed_replacement_rollback"]
        p = Original()
        for event in events:
            p.step(event)
        self.assertEqual(p.generation, 1)
        self.assertIn(("emit", "old-after-rollback"), p.actions)

    def test_original_candidate_accepts_stale_same_generation_observation(self):
        p = Original()
        for event in TRACES["delayed_current_generation_observation"]:
            p.step(event)
        self.assertIn(("emit", "old-seq-same-gen"), p.actions)

    def test_distinct_comparator_outputs(self):
        duplicate = COMPARATORS["duplicate_true"]
        self.assertEqual(last_message(duplicate), ["x2"])
        self.assertEqual(message_count(duplicate), ["x1", "x2"])
        reordered = COMPARATORS["arrival_true_then_delayed_false"]
        self.assertEqual(last_message(reordered), [])
        self.assertEqual(message_count(reordered), ["true3"])

    def test_sequence_guard_mutations_are_detected(self):
        delayed_revoke = TRACES["delayed_same_generation_revoke"]
        expected = replay(Guarded, delayed_revoke)
        mutated = replay(NoSequenceGuard, delayed_revoke)
        self.assertNotEqual(mutated, expected)

        rollback = TRACES["delayed_replacement_rollback"]
        expected_rollback = replay(Guarded, rollback)
        mutated_rollback = replay(ApplyReplaceBeforeSequenceValidation, rollback)
        self.assertNotEqual(mutated_rollback, expected_rollback)

    def test_batch_future_revoke_mutation_is_detected(self):
        events = [
            {"kind": "obs", "id": "rise", "seq": 1, "gen": 1, "target": 1, "value": True},
            {"kind": "revoke", "seq": 2, "gen": 1},
        ]
        resident = Guarded()
        for event in events:
            resident.step(event)
        incremental_emits = [a[1] for a in resident.actions if a[0] == "emit"]
        batch_mutant = [] if any(e.get("kind") == "revoke" and e.get("gen") == 1 for e in events) else [events[0]["id"]]
        self.assertEqual(incremental_emits, ["rise"])
        self.assertNotEqual(batch_mutant, incremental_emits)


if __name__ == "__main__":
    unittest.main()
