"""Excluded synthetic construction tests for Issue #4103."""
from __future__ import annotations
import json, os, tempfile, unittest
from pathlib import Path
from PIL import Image
os.environ.setdefault("AGENT_INTERFACE_ROOT", str(Path(__file__).resolve().parents[3] / "fake_repo"))
from transfer import Frame, VectorEncoder, ContiguousEncoder, reference

class Equivalence(unittest.TestCase):
    def check(self,a,b,w,h):
        before=Frame(w,h,"RGB",a); after=Frame(w,h,"RGB",b)
        encs=[reference.Encoder("s","O2",64),VectorEncoder("s","O2",64),ContiguousEncoder("s","O2",64)]
        wires=[]
        for e in encs:
            w1=e.encode(before,action_id="b",observed_ns=1,context=("x",)); w2=e.encode(after,action_id="a",observed_ns=2,context=("x",)); wires.append((w1,w2))
        self.assertEqual(wires[0],wires[1]); self.assertEqual(wires[1],wires[2])
        for w1,w2 in wires:
            d=reference.Decoder("s"); self.assertEqual(d.accept(w1),before); self.assertEqual(d.accept(w2),after)
    def test_one_pixel(self):
        a=bytes(17*13*3); b=bytearray(a); b[-1]=1; self.check(a,bytes(b),17,13)
    def test_dense(self): self.check(bytes(130*90*3),b"\xff"*(130*90*3),130,90)
    def test_partial_edges(self):
        a=bytes(129*65*3); b=bytearray(a); b[0]=1;b[-1]=2;self.check(a,bytes(b),129,65)
    def test_unchanged(self): self.check(bytes(64*64*3),bytes(64*64*3),64,64)
    def test_png_rgb_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"x.png"; Image.new("RGB",(7,5),(1,2,3)).save(p)
            with Image.open(p) as im: self.assertEqual(im.convert("RGB").tobytes(),bytes([1,2,3])*35)

if __name__=="__main__": unittest.main(verbosity=2)
