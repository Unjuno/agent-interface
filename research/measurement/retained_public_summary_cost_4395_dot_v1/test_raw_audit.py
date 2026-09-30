"""Fabricated measurement-ledger tests. No projection or scientific call occurs."""
import copy
import itertools
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import oracle
import run_once


class RawAuditConstruction(unittest.TestCase):
    def test_fabricated_ledger_and_twelve_effective_controls(self):
        # Deliberately invented clocks/memory prove only validator sensitivity.
        # Input/expected text is retained data; no candidate projection runs.
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)/'source';out=Path(temporary)/'output'
            (root/'inputs').mkdir(parents=True);(out/'outputs').mkdir(parents=True)
            for src in (Path(__file__).parent/'inputs').iterdir():
                shutil.copyfile(src,root/'inputs'/src.name)
            (root/'harness.py').write_text('# construction sentinel, never executed\n')
            hashes={str(f.relative_to(root)):oracle.digest(f.read_bytes()) for f in root.rglob('*') if f.is_file()}
            (root/'FREEZE.json').write_text(json.dumps({'files':hashes,'file_count':len(hashes)}))
            corpus={c:json.loads((root/'inputs'/f'{c}-full.json').read_bytes()) for c in oracle.CASES}
            expected={c:json.loads((root/'inputs'/f'{c}-summary.json').read_bytes()) for c in ('entry','save')}
            raw={'schema':'retained-public-projection-cost-v1','source_hashes':hashes,'freeze_sha256':oracle.digest((root/'FREEZE.json').read_bytes()),'outputs':{},'rows':[],'memory':[],
                'clock':{'empty_brackets':[[10,10] for _ in range(64)],'wall_resolution_ns':1,'cpu_resolution_ns':1,'empty_wall_median_low_ns':10,'empty_cpu_median_low_ns':10,'minimum_ns':1000},
                'inputs_unchanged':True,'input_object_before_sha256':{c:oracle.digest(oracle.canonical(v)) for c,v in corpus.items()},'input_object_after_sha256':{c:oracle.digest(oracle.canonical(v)) for c,v in corpus.items()},
                'counts':{'warmup':54,'measured':162,'memory':9,'total':225},'gui_or_action_dispatches':0}
            for case in oracle.CASES:
                for policy in oracle.POLICIES:
                    value=oracle.expected_view(case,policy,corpus[case],expected.get(case))
                    data=json.dumps(value,allow_nan=False).encode();file='outputs/'+case+'-'+policy+'.json'
                    (out/file).write_bytes(data)
                    raw['outputs'][case+'/'+policy]={'file':file,'sha256':oracle.digest(data),'bytes':len(data)}
                    raw['memory'].append({'case':case,'policy':policy,'net_bytes':1,'peak_bytes':2,'output_sha256':oracle.digest(data)})
            for phase in ('warmup','measured'):
                for case in oracle.CASES:
                    for index,order in enumerate(itertools.permutations(oracle.POLICIES)):
                        for policy in order:
                            count=1 if phase=='warmup' else 3
                            raw['rows'].append({'phase':phase,'case':case,'policy':policy,'order':index,'count':count,'wall_ns':10000,'cpu_ns':10000,'output_sha256s':[raw['outputs'][case+'/'+policy]['sha256']]*count})
            self.assertEqual(oracle.audit(root,out,raw),[])
            controls=run_once.controls(root,out,raw,oracle.audit)
            self.assertEqual(len(controls),12)
            self.assertTrue(all(c['changed_canonical_json'] and c['rejected'] for c in controls))
            for c in controls[:8]:
                self.assertTrue(any('semantic:' in e or 'preserved:' in e or 'source:' in e or 'execution:' in e for e in c['errors']),c)
            self.assertEqual(oracle.audit(root,out,raw),[])

if __name__=='__main__':
    unittest.main()
