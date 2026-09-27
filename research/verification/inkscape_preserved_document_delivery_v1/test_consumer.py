import copy, unittest
from consumer import evaluate,sha

B=b'<svg xmlns="http://www.w3.org/2000/svg" width="320" height="180" viewBox="0 0 320 180"><rect id="target" x="20" y="30" width="40" height="20" fill="#ff00aa"/><rect id="sentinel" x="160" y="80" width="30" height="25" fill="#0080ff"/></svg>\n'
A=B.replace(b'x="20"',b'x="50"')
BQ=b'target,20,30,40,20\nsentinel,160,80,30,25\n'
AQ=BQ.replace(b'target,20,',b'target,50,')
C={'before_sha256':sha(B),'target_id':'target','translation_x':30,'expected_ids':['sentinel','target']}
R={'exit':0,'document_sha256':sha(A)}
class Tests(unittest.TestCase):
    def ev(self,a=A,aq=AQ,c=None,r=None,view='full'):
        return evaluate(B,BQ,a,aq,C if c is None else c,R if r is None else r,view)
    def test_positive(self):self.assertEqual(self.ev()['outcome'],'COMPLETE_SUCCESS')
    def test_style_overrides_attribute(self):
        a=A.replace(b'fill="#0080ff"',b'fill="#0080ff" style="fill:#ff0000"')
        self.assertEqual(self.ev(a=a,r={'exit':0,'document_sha256':sha(a)})['outcome'],'PARTIAL_REQUIRED_EFFECT_ONLY')
    def test_no_effect(self):self.assertEqual(self.ev(a=B,aq=BQ,r={'exit':0,'document_sha256':sha(B)})['outcome'],'FAILURE')
    def test_withheld(self):self.assertEqual(self.ev(view='collateral_withheld')['outcome'],'UNKNOWN')
    def test_bad_digest(self):self.assertEqual(self.ev(r={'exit':0,'document_sha256':'x'})['outcome'],'UNKNOWN')
    def test_bad_input_digest(self):self.assertEqual(self.ev(c={**C,'before_sha256':'x'})['outcome'],'UNKNOWN')
    def test_bool_exit(self):self.assertEqual(self.ev(r={**R,'exit':False})['outcome'],'UNKNOWN')
    def test_bool_translation(self):self.assertEqual(self.ev(c={**C,'translation_x':True})['outcome'],'UNKNOWN')
    def test_missing_target(self):self.assertEqual(self.ev(c={**C,'target_id':'absent'})['outcome'],'UNKNOWN')
    def test_query_mismatch(self):self.assertEqual(self.ev(aq=AQ.replace(b'50',b'51'))['outcome'],'UNKNOWN')
    def test_nan_query(self):self.assertEqual(self.ev(aq=AQ.replace(b'50',b'NaN'))['outcome'],'UNKNOWN')
    def test_duplicate_query(self):self.assertEqual(self.ev(aq=AQ+AQ)['outcome'],'UNKNOWN')
    def test_transform_unmodeled(self):
        a=A.replace(b'id="target"',b'id="target" transform="translate(1,0)"')
        self.assertEqual(self.ev(a=a,r={'exit':0,'document_sha256':sha(a)})['outcome'],'UNKNOWN')
    def test_global_css_is_unknown(self):
        a=A.replace(b'</svg>',b'<style>rect {fill:red}</style></svg>')
        self.assertEqual(self.ev(a=a,r={'exit':0,'document_sha256':sha(a)})['outcome'],'UNKNOWN')
    def test_no_authority(self):self.assertIs(self.ev()['authority'],False)
if __name__=='__main__':unittest.main()
