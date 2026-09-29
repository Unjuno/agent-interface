"""Small construction tests; do not execute the formal matrix."""
import itertools
import unittest
from audit import batch
from reducer import Reducer


def msg(check, value="PASS", rid=None, **patch):
    record = {"rid": rid or check, "check": check, "subject": check,
              "session": "session-vj01", "decision": "decision-vj01", "epoch": 7,
              "role": "VERIFIED_EFFECT" if check == "effect" else "CURRENT", "value": value}
    record.update(patch)
    return record


class Construction(unittest.TestCase):
    def exercise(self, events, expected):
        r = Reducer()
        self.assertEqual(r.view(), "U")
        for i, item in enumerate(events):
            self.assertEqual(r.feed(item), batch(events[:i+1])[0])
        self.assertEqual(r.seal(), expected)
        self.assertIs(r.authority, False)
        self.assertEqual(r.feed(msg("effect", "FAIL", "after-seal")), expected)
        self.assertEqual(r.seal(), expected)

    def test_empty(self):
        self.exercise([], "U")

    def test_positive_no_optional(self):
        self.exercise([msg("effect"), msg("target")], "P")

    def test_optional_not_required(self):
        self.exercise([msg("diagnostic", "UNKNOWN"), msg("target"), msg("effect")], "P")

    def test_role_is_exact(self):
        self.exercise([msg("target"), msg("effect", role="CURRENT")], "U")

    def test_veto(self):
        self.exercise([msg("target", "FAIL"), msg("diagnostic"), msg("effect")], "F")

    def test_conflict(self):
        self.exercise([msg("effect"), msg("target"), msg("target", "FAIL", "other")], "U")

    def test_identity_collision_all_orders(self):
        records = [msg("target", rid="collision"), msg("target", "FAIL", "collision"), msg("effect")]
        for order in itertools.permutations(records):
            self.exercise(list(order), "U")

    def test_duplicate(self):
        x = msg("target", rid="duplicate")
        self.exercise([x, x.copy(), msg("effect")], "P")

    def test_foreign_does_not_poison(self):
        self.exercise([msg("target"), msg("effect"), msg("target", "FAIL", epoch=9)], "P")

    def test_malformed(self):
        for bad in (None, [], {}, msg("target", epoch=True), msg("target", value=[])):
            self.exercise([msg("effect"), bad], "U")

    def test_provisional_is_not_final(self):
        r = Reducer()
        r.feed(msg("target")); r.feed(msg("effect"))
        self.assertEqual(r.view(), "P")
        self.assertEqual(r.feed(msg("target", "FAIL", "contradiction")), "U")
        self.assertEqual(r.seal(), "U")

    def test_no_authority_field(self):
        self.exercise([msg("target", authority=True), msg("effect")], "U")


if __name__ == "__main__":
    unittest.main(verbosity=2)
