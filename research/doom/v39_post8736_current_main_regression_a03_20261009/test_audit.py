import copy
import json
from pathlib import Path
import unittest
import importlib.util
import hashlib
import tempfile

spec=importlib.util.spec_from_file_location("v39_a03_saved_audit", Path(__file__).with_name("audit.py"))
audit=importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

HERE=Path(__file__).resolve().parent
FREEZE=json.loads((HERE/'FREEZE.json').read_text())
RESULT=json.loads((HERE/'RESULT.json').read_text())
CLOSURE=json.loads((HERE/'results/source-closure-audit.json').read_text())
RECEIPTS=json.loads((HERE/'results/exit-codes.json').read_text())
LOGS={mode:(HERE/'results'/f'{mode}.log').read_text() for mode in ('normal','optimized')}

class SavedEvidenceAuditTests(unittest.TestCase):
    def test_package_hash_manifest_passes(self):
        self.assertTrue(audit.verify_hash_manifest(HERE))

    def test_frozen_package_passes(self):
        checks=audit.verify_records(FREEZE,RESULT,CLOSURE,RECEIPTS,LOGS)
        self.assertTrue(all(checks.values()),checks)

    def test_foreign_closure_commit_is_rejected(self):
        closure=copy.deepcopy(CLOSURE); closure['source_commit']='b4046798ed8902745a36e8fda091204233bb06d3'
        self.assertFalse(audit.verify_records(FREEZE,RESULT,closure,RECEIPTS,LOGS)['exact_frozen_commit'])

    def test_foreign_allocation_result_is_rejected(self):
        result=copy.deepcopy(RESULT); result['allocation_id']='forged-allocation'
        self.assertFalse(audit.verify_records(FREEZE,result,CLOSURE,RECEIPTS,LOGS)['allocation_identity'])

    def test_closure_recount_cannot_be_forged(self):
        closure=copy.deepcopy(CLOSURE); closure['closure_entries']=72
        self.assertFalse(audit.verify_records(FREEZE,RESULT,closure,RECEIPTS,LOGS)['closure_linkage'])

    def test_scope_promotion_is_rejected(self):
        freeze=copy.deepcopy(FREEZE); freeze['scope']['live_allocation']=True
        self.assertFalse(audit.verify_records(freeze,RESULT,CLOSURE,RECEIPTS,LOGS)['scope_consistency'])

    def test_receipt_and_log_mismatch_is_rejected(self):
        receipts=copy.deepcopy(RECEIPTS); receipts['normal_exit']=1
        self.assertFalse(audit.verify_records(FREEZE,RESULT,CLOSURE,receipts,LOGS)['exit_receipt'])
        logs=dict(LOGS); logs['optimized']=logs['optimized'].replace('Ran 107 tests','Ran 106 tests')
        self.assertFalse(audit.verify_records(FREEZE,RESULT,CLOSURE,RECEIPTS,logs)['optimized_test_receipt'])

    def test_hash_manifest_rejects_corruption_and_omission(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            payload=root/'evidence.txt'
            payload.write_text('frozen evidence\n')
            digest=hashlib.sha256(payload.read_bytes()).hexdigest()
            manifest=root/'SHA256SUMS.txt'
            manifest.write_text(f'{digest}  ./evidence.txt\n')
            self.assertTrue(audit.verify_hash_manifest(root))
            payload.write_text('corrupted evidence\n')
            self.assertFalse(audit.verify_hash_manifest(root))
            payload.write_text('frozen evidence\n')
            manifest.write_text('')
            self.assertFalse(audit.verify_hash_manifest(root))

    def test_hash_manifest_rejects_duplicate_and_escaping_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            payload=root/'evidence.txt'
            payload.write_text('frozen evidence\n')
            digest=hashlib.sha256(payload.read_bytes()).hexdigest()
            manifest=root/'SHA256SUMS.txt'
            entry=f'{digest}  ./evidence.txt\n'
            manifest.write_text(entry+entry)
            self.assertFalse(audit.verify_hash_manifest(root))
            manifest.write_text(f'{digest}  ./../outside.txt\n')
            self.assertFalse(audit.verify_hash_manifest(root))

if __name__=='__main__': unittest.main(verbosity=2)
