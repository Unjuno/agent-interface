import json
import unittest
from pathlib import Path
from candidate import run
ROOT = Path(__file__).parent
class CandidateConstruction(unittest.TestCase):
    def test_emits_exact_visible_grid(self):
        v=json.loads((ROOT/'visible.json').read_text())
        raw=run(v)
        expected=sum(len(o['ticks']) for o in v['assigned_opportunities'])
        self.assertEqual(len(raw['rows']), expected)
        self.assertEqual(len({(r['opportunity_id'],r['route'],r['tick']) for r in raw['rows']}),expected)
if __name__=='__main__': unittest.main()
