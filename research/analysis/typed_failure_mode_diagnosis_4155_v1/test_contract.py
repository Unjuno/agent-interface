import unittest
import experiment as e

class ContractTests(unittest.TestCase):
    def row(self,focus="CURRENT",target="CURRENT",modal="ABSENT",app="IDLE",variation=0):
        return {"focus":focus,"target":target,"modal":modal,"app":app,"variation":variation}
    def test_four_identifiable_modes(self):
        cases=[
            (self.row(focus="LOST"),"FOCUS_LOST","REBIND"),
            (self.row(target="STALE"),"TARGET_STALE","YIELD"),
            (self.row(modal="PRESENT"),"MODAL_BLOCKED","RETRY_BOUNDED"),
            (self.row(app="PENDING"),"APP_BUSY_OR_PENDING","WAIT_OBSERVE"),
        ]
        for r,m,d in cases:
            self.assertEqual(e.mode_then_recovery(r),(m,d)); self.assertEqual(e.direct_recovery(r),d); self.assertEqual(e.oracle(r),(m,d,True))
    def test_unknown_and_contradiction_yield(self):
        for r in [self.row(focus="UNKNOWN"), self.row(focus="LOST",modal="PRESENT"), self.row()]:
            self.assertEqual(e.direct_recovery(r),"YIELD"); self.assertEqual(e.mode_then_recovery(r)[1],"YIELD"); self.assertEqual(e.oracle(r)[1],"YIELD")
    def test_variation_irrelevant(self):
        base=self.row(focus="LOST")
        vals=[]
        for v in range(4): vals.append((e.direct_recovery({**base,"variation":v}),e.mode_then_recovery({**base,"variation":v})))
        self.assertEqual(len(set(vals)),1)
    def test_no_authority_in_formal_row_shape(self):
        first=next(e.rows()); self.assertIs(first["semantic_authority"],False); self.assertIs(first["input_authority"],False)

if __name__=='__main__': unittest.main(verbosity=2)
