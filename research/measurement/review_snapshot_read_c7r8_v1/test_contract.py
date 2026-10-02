"""Disjoint small construction tests, never a formal timing rerun."""
import copy,json,tempfile,unittest
from pathlib import Path
from fixture import create,canon
from worker import FUNCS,counted
from audit import Checks,output,png_pixels,expected_pixels


class Contract(unittest.TestCase):
    def test_stable_bytes_and_read_counts(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'input';create(root,11,9,6)
            raw=(root/'report.json').read_bytes();b={}
            for p,f in FUNCS.items():
                b[p],reads=counted(f,raw,root);self.assertEqual(len(reads),2 if p=='baseline' else 1)
            self.assertEqual(b['baseline'],b['candidate'])
    def test_control_parity_and_preserved_diagnostics(self):
        for con in ['missing','digest_mismatch','no_observation','partial_release_failed']:
            with self.subTest(con=con),tempfile.TemporaryDirectory() as d:
                root=Path(d)/'in';create(root,11,9,6,con);raw=(root/'report.json').read_bytes()
                outs=[canon(f(raw,root)) for f in FUNCS.values()];self.assertEqual(*outs)
                img=(root/'capture.png').read_bytes() if (root/'capture.png').exists() else None
                c=Checks();output(c,outs[0],raw,img,con,'unit');self.assertEqual(c.errors,[])
    def test_independent_pixel_decoder(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d)/'in';create(r,11,9,6);w,h,p=png_pixels((r/'capture.png').read_bytes())
            self.assertEqual((w,h),(11,9));self.assertEqual(p,expected_pixels(w,h))
    def test_semantic_mutation_detection(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d)/'in';create(r,11,9,6);raw=(r/'report.json').read_bytes();img=(r/'capture.png').read_bytes()
            good=FUNCS['candidate'](raw,r)
            for field,value in [('authority','input'),('image_status','no_observation')]:
                bad=copy.deepcopy(good);bad[field]=value;c=Checks();output(c,canon(bad),raw,img,'partial_release_failed','mutation')
                self.assertTrue(c.errors)
    def test_release_boolean_not_rewritten(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d)/'in';create(r,11,9,6);raw=(r/'report.json').read_bytes();good=FUNCS['candidate'](raw,r)
            self.assertIs(good['outcome_summary']['input_release_verified'],False)
            self.assertIs(good['outcome_summary']['recovery_required'],True)
    def test_no_runtime_api_import(self):
        import sys
        self.assertNotIn('runtime.cli_v1.api',sys.modules)


if __name__=='__main__':unittest.main()
