"""Mutation controls for the retained finite audit; no live input or model."""
import copy, importlib.util, json, shutil, tempfile, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('retained_audit',HERE/'audit.py'); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
def modify(path,fn):
    row=json.loads(path.read_text()); fn(row); path.write_text(json.dumps(row))
class AuditTests(unittest.TestCase):
    def test_original(self): self.assertEqual(module.audit(HERE)['positive']['independent_save_count'],1)
    def mutation(self,fn):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for name in ('positive','changed'): shutil.copytree(HERE/name,root/name)
            fn(root)
            with self.assertRaises(ValueError): module.audit(root)
    def test_duplicate_save(self):
        def change(root):
            p=root/'positive/events.jsonl'; events=[json.loads(l) for l in p.read_text().splitlines()]; p.write_text(p.read_text()+json.dumps([e for e in events if e['event']=='save'][0])+'\n')
        self.mutation(change)
    def test_wrong_saved_token(self):
        def change(root):
            p=root/'positive/events.jsonl'; rows=[json.loads(l) for l in p.read_text().splitlines()]
            for row in rows:
                if row['event']=='save': row['value']='wrong'
            p.write_text(''.join(json.dumps(r)+'\n' for r in rows))
        self.mutation(change)
    def test_extra_input_program(self):
        self.mutation(lambda root:shutil.copyfile(next((root/'changed/bridge').glob('program-*.json')),root/'changed/bridge/program-replay.json'))
    def test_unverified_release(self):
        self.mutation(lambda root:modify(next((root/'positive/bridge').glob('compiled-*-execution.json')),lambda r:r['result']['execution']['releases'][0].update(verified=False)))
    def test_renewed_program_deadline(self):
        self.mutation(lambda root:modify(next((root/'positive/bridge').glob('program-*.json')),lambda r:r['authority'].update(expires_at_ns=10**30)))
    def test_fabricated_predicate(self):
        self.mutation(lambda root:modify(root/'positive/replies/004.json',lambda r:r['reply']['observations'][0]['predicates'].update(saved_cue=True)))
    def test_image_digest_mismatch(self):
        self.mutation(lambda root:modify(root/'positive/bridge/observation-2.json',lambda r:r['native']['artifact'].update(sha256='0'*64)))
if __name__=='__main__':unittest.main()
