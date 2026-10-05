import json
from pathlib import Path
import tempfile
import unittest
from verify_packet import ROOT, corruptions, manifest_errors, sha

class RetainedTests(unittest.TestCase):
    def test_saved_recovery_corruptions(self):
        raw=json.loads((ROOT/'retained/recovery01-candidate-data/candidate_stdout.json').read_bytes())
        rejected=corruptions(raw)
        self.assertEqual(len(rejected),9)
        self.assertTrue(all(rejected.values()),rejected)

    def test_manifest_rejects_paths_duplicates_missing_and_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); file=root/'data'; file.write_bytes(b'evidence')
            line=sha(file)+'  data'
            self.assertEqual(manifest_errors(root,[line]),[])
            for invalid in ('../data','/data','C:/data','a\\data','SHA256SUMS'):
                self.assertIn('unsafe_manifest_path',manifest_errors(root,[sha(file)+'  '+invalid]))
            self.assertIn('duplicate_manifest_path',manifest_errors(root,[line,line]))
            self.assertIn('incomplete_manifest',manifest_errors(root,[]))
            file.write_bytes(b'changed')
            self.assertIn('manifest_hash:data',manifest_errors(root,[line]))

if __name__=='__main__': unittest.main()

