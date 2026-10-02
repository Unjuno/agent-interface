import json,shutil,tempfile,unittest
from pathlib import Path
from verify import verify_cases
ROOT=Path(__file__).resolve().parent.parent
class AuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        for case in ['normal-compiled','short-compiled']:
            for path in (ROOT/case).rglob('*'):
                if path.is_file() and path.suffix in ['.json','.png','.svg'] and not any(x in path.parts for x in ['home','cache','config','data','__pycache__']):
                    dest=self.root/path.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
        base=self.root/'normal-compiled';self.bridge=base/json.loads((base/'owner.json').read_text())['bridge_relative']
    def change(self,path,fn):
        data=json.loads(path.read_text());fn(data);path.write_text(json.dumps(data))
    def test_retained_failure_and_capture_accounting(self):
        result=verify_cases(self.root);self.assertEqual(result['physical_captures'],14);self.assertEqual(result['accepted_observations'],13)
    def test_missing_accepted_capture(self):
        (self.bridge/'observation-6.json').unlink()
        with self.assertRaisesRegex(ValueError,'accepted observation count'):verify_cases(self.root)
    def test_capture_cannot_grant_authority(self):
        self.change(next(self.bridge.glob('public-observation-*.json')),lambda d:d.update(side_effect_authority=True))
        with self.assertRaisesRegex(ValueError,'no authority'):verify_cases(self.root)
    def test_rejected_image_cannot_be_final_authority(self):
        self.change(self.root/'normal-compiled/owner-compiled-result.json',lambda d:d['feedback'].update(image={'type':'image'}))
        with self.assertRaisesRegex(ValueError,'withheld'):verify_cases(self.root)
    def test_pending_selection_cannot_be_relabeled_move(self):
        self.change(self.root/'normal-compiled/owner-compiled-result.json',lambda d:d['method_receipt']['pending_effect'].update(action='move'))
        with self.assertRaisesRegex(ValueError,'unresolved select'):verify_cases(self.root)
    def test_rejected_frame_identity_is_verified(self):
        event=json.loads(next(self.bridge.glob('capture-binding-changed-*.json')).read_text());report=json.loads((self.bridge/event['public_report']).read_text());path=self.root/'normal-compiled/compiled-call/images'/Path(report['observation']['artifact']['path']).name;path.write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError,'PNG identity'):verify_cases(self.root)
    def test_saved_file_independent_of_score_claim(self):
        (self.root/'short-compiled/two-rectangles.svg').write_text('altered')
        with self.assertRaisesRegex(ValueError,'actual saved SVG identity'):verify_cases(self.root)
if __name__=='__main__':unittest.main()
