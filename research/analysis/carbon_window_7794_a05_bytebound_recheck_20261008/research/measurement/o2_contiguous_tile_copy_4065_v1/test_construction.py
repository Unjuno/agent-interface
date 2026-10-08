"""Small synthetic tests only. No retained-corpus performance measurements."""
import unittest
from candidate import Frame,VectorEncoder,reference
from contiguous import ContiguousEncoder

class Equivalence(unittest.TestCase):
    def check(self,frames,size=4,strategy='O2'):
        encs=[c('construction',strategy,size) for c in [reference.Encoder,VectorEncoder,ContiguousEncoder]]
        decs=[reference.Decoder('construction') for _ in encs]
        for i,f in enumerate(frames):
            kw=dict(action_id=str(i),observed_ns=i+1,context=('synthetic',))
            wires=[e.encode(f,**kw) for e in encs]
            self.assertEqual(wires[0],wires[1]);self.assertEqual(wires[1],wires[2])
            for d,p in zip(decs,wires):self.assertEqual(d.accept(p),f)
    def test_all_channels(self):
        for mode,c in [('L',1),('RGB',3),('RGBA',4)]:
            a=bytes(7*5*c)
            for i in range(len(a)):
                b=bytearray(a);b[i]=123
                self.check([Frame(7,5,mode,a),Frame(7,5,mode,bytes(b))])
    def test_unchanged(self):self.check([Frame(5,3,'RGB',bytes(45))]*2)
    def test_dense(self):self.check([Frame(13,9,'RGB',bytes(351)),Frame(13,9,'RGB',b'\xff'*351)])
    def test_large_tile(self):self.check([Frame(2,3,'L',bytes(6)),Frame(2,3,'L',bytes([0,0,0,0,0,1]))],64)
    def test_mode_change(self):self.check([Frame(7,5,'L',bytes(35)),Frame(7,5,'RGB',bytes(105))])
    def test_resize(self):self.check([Frame(7,5,'L',bytes(35)),Frame(8,5,'L',bytes(40))])
    def test_o1(self):self.check([Frame(7,5,'L',bytes(35)),Frame(7,5,'L',b'\xff'*35)],4,'O1')
    def test_one_pixel(self):self.check([Frame(1,1,'RGBA',bytes(4)),Frame(1,1,'RGBA',b'\xff'*4)],1)
if __name__=='__main__':unittest.main(verbosity=2)
