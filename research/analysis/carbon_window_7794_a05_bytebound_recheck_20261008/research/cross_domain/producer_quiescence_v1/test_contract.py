import tempfile,unittest
from pathlib import Path
from PIL import Image
from contract import image_receipt,sha
A=bytes([1,2,3])*4;B=bytes([4,5,6])*4
class T(unittest.TestCase):
    def exp(self):return {'a_rgb_sha256':sha(A),'b_rgb_sha256':sha(B)}
    def test_absent(self):
        with tempfile.TemporaryDirectory() as d:self.assertEqual(image_receipt(Path(d)/'x.png',self.exp())['state'],'ABSENT')
    def test_a_b_other(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.png'
            for pix,want in [((1,2,3),'A'),((4,5,6),'B'),((7,8,9),'OTHER')]:
                Image.new('RGB',(2,2),pix).save(p);self.assertEqual(image_receipt(p,self.exp())['state'],want)
if __name__=='__main__':unittest.main()
