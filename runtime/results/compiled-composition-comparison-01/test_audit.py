"""Finite audit mutation controls, with no GUI/model/input/re-allocation."""
import importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('audit',HERE/'audit.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
def change(p,fn):
    r=json.loads(p.read_text()); fn(r); p.write_text(json.dumps(r))
class Tests(unittest.TestCase):
    def test_original(self): self.assertEqual(len(m.audit(HERE)),4)
    def mutation(self,fn):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td); shutil.copyfile(HERE/'ALLOCATION.json',p/'ALLOCATION.json')
            for case in json.loads((p/'ALLOCATION.json').read_text())['cases']: shutil.copytree(HERE/case['name'],p/case['name'])
            fn(p)
            with self.assertRaises(ValueError): m.audit(p)
    def test_false_changed_success(self): self.mutation(lambda p:change(p/'04-changed-form/bridge/method-common.json',lambda r:r.update(outcome='TASK_SUCCEEDED')))
    def test_duplicate_save(self):
        def modify(p):
            f=p/'01-positive-form/events.jsonl'; rows=[json.loads(l) for l in f.read_text().splitlines()]; f.write_text(f.read_text()+json.dumps([r for r in rows if r['event']=='save'][0])+'\n')
        self.mutation(modify)
    def test_nonneutral_release(self): self.mutation(lambda p:change(next((p/'01-positive-form/bridge').glob('result-*.json')),lambda r:r['execution']['releases'][0].update(verified=False)))
    def test_changed_input_program(self):
        def modify(p):
            f=next((p/'02-positive-compiled/bridge').glob('program-*.json'))
            def mutate(r):
                for op in r['ops']:
                    if op['op']=='pointer_move':op['x']+=1
            change(f,mutate)
        self.mutation(modify)
    def test_false_predicate(self): self.mutation(lambda p:change(p/'02-positive-compiled/bridge/method-raw.json',lambda r:r['observations'][1]['predicates'].update(submit_present=False)))
    def test_renewed_deadline(self): self.mutation(lambda p:change(next((p/'01-positive-form/bridge').glob('program-*.json')),lambda r:r['authority'].update(expires_at_ns=10**30)))
    def test_image_digest(self): self.mutation(lambda p:change(p/'01-positive-form/bridge/observation-2.json',lambda r:r['native']['artifact'].update(sha256='0'*64)))
if __name__=='__main__':unittest.main()
