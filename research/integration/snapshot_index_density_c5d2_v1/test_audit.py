"""Construction validation and semantic corruptions of the excluded raw example."""
import json,unittest
from pathlib import Path
from audit import check,mutations
class Checks(unittest.TestCase):
    def setUp(self):
        p=Path(__file__).parent/'construction-01';self.data=(p/'input.jsonl').read_bytes();self.raw=json.loads((p/'stdout.json').read_bytes())
    def test_original_construction(self):check(self.raw,self.data,16,0)
    def test_ten_semantic_corruptions(self):
        r=mutations([(self.raw,self.data,16,0)]);self.assertEqual(len(r),10);self.assertTrue(all(x['rejected'] for x in r))
if __name__=='__main__':unittest.main()
