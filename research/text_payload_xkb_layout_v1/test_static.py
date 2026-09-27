import hashlib, json, unittest
from pathlib import Path
from xkb_projection import project_group1_two_levels
HERE=Path(__file__).resolve().parent
class T(unittest.TestCase):
    def test_dependency_blob(self):
        p=HERE/'preflight_dependency.py'; d=p.read_bytes(); self.assertEqual(hashlib.sha1(b'blob '+str(len(d)).encode()+b'\0'+d).hexdigest(),'35c7375e50f3e0c58f57c8139a6dc8abeef87771')
    def test_schedule_frozen(self):
        import run_matrix; self.assertEqual(run_matrix.SCHEDULE,[('us',''),('de',''),('fr',''),('us','dvorak')])
    def test_parser_handles_same_line_and_multiline(self):
        x='''<LFSH> = 50;\n<AE01> = 10;\nkey <LFSH> { [ Shift_L ] };\nkey <AE01> {\n symbols[Group1]= [ 1, exclam ]\n};'''
        current=[[0,0] for _ in range(60)]; rows,n=project_group1_two_levels(x,8,current); self.assertEqual(n,2); self.assertEqual(rows[42][0],0xffe1); self.assertEqual(rows[2],[49,33])
if __name__=='__main__': unittest.main()
