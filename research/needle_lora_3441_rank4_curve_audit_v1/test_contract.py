"""Construction-only tests; do not invoke the full predecessor audit here."""
import ast,pathlib,unittest

ROOT=pathlib.Path(__file__).resolve().parent
SOURCE=(ROOT/"audit_curves.py").read_text(encoding="utf-8")
TREE=ast.parse(SOURCE)

class CurveAuditContract(unittest.TestCase):
    def test_source_parses_and_pins_exact_predecessor(self):
        ast.parse(SOURCE)
        for pin in ("F185E4DEAB4B19BA4B146C723CB03C1078DB53307DCBF1C2D856D9C5728C320E","7b2547439420aa991668cbffe29eb296a9fc4e921663e3d51053441522ce443b","1FE0A27E045085508478FCCEA1DAAF3096BA0F2775A6A9F8C1A693536579554F","82AD70186A9FAEB59350B8CA1C9E951101D40C1C99DBA6EBB6BE4519187F800F"):
            self.assertIn(pin,SOURCE)
    def test_frozen_seed_and_balanced_order(self):
        self.assertIn("SEEDS=(3451,3452,3453,3454,3455)",SOURCE)
        self.assertIn("torch.randperm(16,generator=torch.Generator(device=\"cpu\").manual_seed(seed+30))",SOURCE)
        self.assertIn("curve_rows!=160",SOURCE)
    def test_audit_is_cpu_only_and_offline(self):
        self.assertNotIn(".cuda(",SOURCE)
        self.assertNotIn("torch.optim",SOURCE)
        self.assertNotIn("subprocess",SOURCE)
        self.assertNotIn("urlopen",SOURCE)
    def test_accuracy_helper_is_strict(self):
        ns={"__name__":"test_module"}
        exec(compile(TREE,str(ROOT/"audit_curves.py"),"exec"),ns)
        self.assertEqual(ns["accuracy"]([1,2,3,0],[1,0,3,0]),.75)
        with self.assertRaises(ValueError):ns["accuracy"]([1],[1,2])
        with self.assertRaises(ValueError):ns["accuracy"]([],[])
if __name__=="__main__":unittest.main()
