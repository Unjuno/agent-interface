import hashlib
from pathlib import Path
import tempfile
import unittest
from verify_packet import manifest_errors, run_errors


class RetainedTests(unittest.TestCase):
    def test_complete_manifest_and_nested_manifest_are_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'exact.bin').write_bytes(b'exact\r\n\x00')
            line=hashlib.sha256((root/'exact.bin').read_bytes()).hexdigest()+'  exact.bin'
            self.assertEqual(manifest_errors(root,[line]),[])
            self.assertTrue(manifest_errors(root,[]))
            self.assertTrue(manifest_errors(root,[line,line]))
            self.assertTrue(manifest_errors(root,['0'*64+'  ../other']))
            (root/'nested').mkdir();(root/'nested/SHA256SUMS').write_text('not root')
            self.assertTrue(manifest_errors(root,[line]))

    def test_summary_count_type_hypothesis_and_scope(self):
        audit={'status':'METHOD_PASS_CONSTRUCTION_ONLY','hypothesis':'H_PASS_BOUNDARY_CONSTRUCTION_ONLY',
               'rows':8,'old_stamp_expired':{'PUBLISH_DELAY':4,'READER_DELAY':4},'scope':'construction'}
        run={'disposition':audit['status'],'hypothesis':audit['hypothesis'],'rows':8,
             'old_stamp_expired':audit['old_stamp_expired'],'scope':'construction',
             'candidate_invocations':1,'auditor_invocations':1,'retries':0,'GUI_input':0}
        self.assertEqual(run_errors(run,audit),[])
        for field,value in [('candidate_invocations',True),('hypothesis','GENERAL_PASS'),
                            ('rows',9),('scope','A05_cause')]:
            self.assertTrue(run_errors({**run,field:value},audit))


if __name__=='__main__':unittest.main()
