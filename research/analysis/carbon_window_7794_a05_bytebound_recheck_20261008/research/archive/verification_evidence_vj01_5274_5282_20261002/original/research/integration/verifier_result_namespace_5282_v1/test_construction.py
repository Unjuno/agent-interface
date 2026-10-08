import unittest
from probe import evaluate
from audit import oracle


def event(producer, check, value="PASS", rid="construction"):
    return dict(producer=producer, check=check, subject=check, rid=rid,
                session="session-vj01", decision="decision-vj01", epoch=7,
                role="VERIFIED_EFFECT" if check=="effect" else "CURRENT", value=value)


class Construction(unittest.TestCase):
    def test_cross_producer_collision(self):
        e=[event("alpha","target"),event("beta","effect")]
        self.assertEqual(evaluate(e,False)["final"],"U")
        self.assertEqual(evaluate(e,True)["final"],"P")
        self.assertEqual(oracle(e,True),"P")
    def test_same_producer_conflict(self):
        e=[event("alpha","target"),event("alpha","target","FAIL"),event("beta","effect")]
        self.assertEqual(evaluate(e,True)["final"],"U")
        self.assertEqual(oracle(e,True),"U")
    def test_wrong_producer(self):
        e=[event("beta","target"),event("beta","effect")]
        self.assertEqual(evaluate(e,True)["final"],"U")
    def test_exact_retry(self):
        e=[event("alpha","target"),event("beta","effect"),event("alpha","target")]
        self.assertEqual(evaluate(e,True)["final"],"P")
    def test_unsupported(self):
        for e in [[],[None],[{}],[event("unknown","target")]]:
            self.assertEqual(evaluate(e,True)["final"],"U")
    def test_late_historical_seal(self):
        r=evaluate([event("alpha","target"),event("beta","effect")],True)
        self.assertEqual(r["late"],"PP"); self.assertIs(r["authority"],False)


if __name__=="__main__": unittest.main(verbosity=2)
