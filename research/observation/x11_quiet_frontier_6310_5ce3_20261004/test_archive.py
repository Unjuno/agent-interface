import hashlib,json,unittest
from pathlib import Path
ROOT=Path(__file__).parent
class ArchiveTests(unittest.TestCase):
    def test_first_stop_and_saved_qualification_preserved(self):
        frozen=json.loads((ROOT/'FREEZE.json').read_text())
        for name,digest in frozen['sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest,name)
        candidate=json.loads((ROOT/'runs/candidate/receipt.json').read_text())
        auditor=json.loads((ROOT/'runs/auditor/receipt.json').read_text())
        self.assertEqual(candidate['terminal']['ExitCode'],0)
        self.assertEqual(auditor['terminal']['ExitCode'],1)
        self.assertFalse(candidate['terminal']['Running']);self.assertFalse(auditor['terminal']['Running'])
        first=json.loads((ROOT/'runs/auditor/AUDIT.json').read_text())
        self.assertEqual(first['status'],'STOP_INVALID_NATIVE_EVIDENCE')
        self.assertEqual(first['error'],"ValueError('effective control')")
        saved=json.loads((ROOT/'validation/AUDIT_SAVED_V2.json').read_text())
        self.assertEqual((saved['cells'],saved['naive_stale_journal_false_quiet'],saved['endpoint_equality_false_quiet'],saved['qualified_false_quiet']),(15,9,6,0))
        self.assertEqual(saved['unknown_missing_subscription'],3)
        self.assertEqual(saved['quiet_F_changed_before_B'],3)
        self.assertEqual(len(saved['controls']),8);self.assertTrue(all(c['rejected']for c in saved['controls']))
        self.assertEqual(hashlib.sha256((ROOT/'runs/candidate/raw.jsonl').read_bytes()).hexdigest(),first['raw_sha256'])
if __name__=='__main__':unittest.main()
