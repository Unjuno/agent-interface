"""Construction-only checks: uses seeds disjoint from every registered allocation."""
import contextlib, hashlib, importlib.util, io, json, os, tempfile, unittest
from pathlib import Path

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location("candidate",HERE/"experiment.py")
candidate=importlib.util.module_from_spec(spec); spec.loader.exec_module(candidate)
audit_spec=importlib.util.spec_from_file_location("independent_audit",HERE/"audit.py")
audit=importlib.util.module_from_spec(audit_spec); audit_spec.loader.exec_module(audit)

class Construction(unittest.TestCase):
    def test_alternate_seed_reproducibility_and_balance(self):
        original=(candidate.TRAIN_SEED,candidate.TEST_SEED)
        self.assertEqual(original,(866309294,301332595))
        self.assertEqual(audit.SEEDS,(866309294,301332595))
        self.assertEqual(audit.ALLOCATION,"typed-mode-4844-successor-20260928-04")
        candidate.TRAIN_SEED,candidate.TEST_SEED=59003,59004
        try:
            digests=[]
            for _ in range(2):
                with tempfile.TemporaryDirectory() as d:
                    os.environ["OUT_DIR"]=d
                    with contextlib.redirect_stdout(io.StringIO()): candidate.main()
                    raw=(Path(d)/"result.json").read_bytes(); obj=json.loads(raw)
                    digests.append(hashlib.sha256(raw).hexdigest())
                    self.assertEqual((obj["seed_train"],obj["seed_test"]),(59003,59004))
                    self.assertEqual(obj["allocation"],"typed-mode-4844-successor-20260928-04")
                    self.assertEqual(obj["n_train"],2000)
                    self.assertEqual(obj["n_test"],4800)
                    self.assertEqual([obj["blocks"][b]["n"] for b in candidate.BLOCKS],[960]*5)
                    self.assertEqual([sum(r["mode"]==m for r in obj["rows"] if r["block"]=="COMPLETE") for m in range(5)],[192]*5)
                    self.assertTrue(all(r["truth"]==candidate.DISP[r["mode"]] for r in obj["rows"]))
            self.assertEqual(digests[0],digests[1])
            old_audit_seeds=audit.SEEDS
            audit.SEEDS=(59003,59004)
            try:
                receipt=audit.audit_bytes(raw,hashlib.sha256(raw).hexdigest())
                self.assertTrue(receipt["pass"])
                self.assertEqual(receipt["corruption_controls_rejected"],16)
                self.assertIn("disposition",receipt["decision"])
                with self.assertRaises(ValueError):
                    audit.audit_bytes(raw+b" ",hashlib.sha256(raw+b" ").hexdigest())
                dup=raw.replace(b'"allocation":',b'"allocation":"duplicate","allocation":',1)
                with self.assertRaises(ValueError):
                    audit.audit_bytes(dup,hashlib.sha256(dup).hexdigest())
            finally:
                audit.SEEDS=old_audit_seeds
        finally:
            candidate.TRAIN_SEED,candidate.TEST_SEED=original
            os.environ.pop("OUT_DIR",None)

if __name__=="__main__": unittest.main(verbosity=2)
