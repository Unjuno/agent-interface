"""Construction-only codec invariants on tiny inputs, not timing samples."""
import unittest
import numpy as np
from codec import Frame, Encoder, DenseEncoder, Decoder
from audit import decode

class Tests(unittest.TestCase):
    def test_modes_and_edges(self):
        for mode,channels in [('RGB',3),('RGBA',4),('L',1)]:
            for width,height in [(7,5),(65,67),(130,3)]:
                before=Frame(width,height,mode,bytes(width*height*channels))
                b=bytearray(before.pixels);b[-1]=17
                after=Frame(width,height,mode,bytes(b))
                for cls in (Encoder,DenseEncoder):
                    e=cls('unit');d=Decoder('unit')
                    f=e.encode(before,action_id='a',observed_ns=1)
                    p=e.encode(after,action_id='b',observed_ns=2)
                    self.assertEqual(d.accept(f),before)
                    self.assertEqual(d.accept(p),after)
                    self.assertEqual(decode(p,decode(f)[1])[1],after.pixels)
    def test_sparse_packet_identity(self):
        a=Frame(65,67,'RGB',bytes(65*67*3));b=bytearray(a.pixels);b[0]=1;b=Frame(65,67,'RGB',bytes(b))
        packets=[]
        for cls in (Encoder,DenseEncoder):
            e=cls('unit');e.encode(a,action_id='a',observed_ns=1)
            packets.append(e.encode(b,action_id='b',observed_ns=2))
        self.assertEqual(*packets)
    def test_unchanged_identity(self):
        a=Frame(7,5,'RGB',bytes(105));packets=[]
        for cls in (Encoder,DenseEncoder):
            e=cls('unit');e.encode(a,action_id='a',observed_ns=1)
            packets.append(e.encode(a,action_id='b',observed_ns=2))
            self.assertEqual(e.last['kind'],'unchanged')
        self.assertEqual(*packets)
    def test_all_dirty_exact_full(self):
        a=Frame(65,67,'RGB',bytes(65*67*3));b=Frame(65,67,'RGB',bytes([19])*len(a.pixels))
        e=DenseEncoder('unit');e.encode(a,action_id='a',observed_ns=1)
        p=e.encode(b,action_id='b',observed_ns=2)
        self.assertEqual(decode(p)[1],b.pixels);self.assertEqual(e.last['kind'],'full')
    def test_serialization_failure_state(self):
        for cls in (Encoder,DenseEncoder):
            e=cls('unit');a=Frame(7,5,'L',bytes(35));e.encode(a,action_id='a',observed_ns=1)
            old=e.previous;last=e.last.copy()
            with self.assertRaises(TypeError):e.encode(a,action_id='b',observed_ns=2,context=object())
            self.assertIs(e.previous,old);self.assertEqual(e.sequence,1);self.assertEqual(e.last,last)
    def test_resize_mode_and_followup(self):
        for cls in (Encoder,DenseEncoder):
            e=cls('unit');d=Decoder('unit')
            for i,f in enumerate([Frame(7,5,'L',bytes(35)),Frame(8,5,'L',bytes(40)),Frame(8,5,'RGB',bytes(120))]):
                p=e.encode(f,action_id='a',observed_ns=i);self.assertEqual(d.accept(p),f)
                self.assertEqual(e.last['kind'],'full')
    def test_o1_unchanged_behavior(self):
        a=Frame(7,5,'L',bytes(35));b=Frame(7,5,'L',bytes([1])*35)
        e=Encoder('u','O1');f=DenseEncoder('u','O1')
        for i,frame in enumerate([a,b,b]):
            self.assertEqual(e.encode(frame,action_id='a',observed_ns=i),f.encode(frame,action_id='a',observed_ns=i))
    def test_invalid_construction(self):
        for cls in (Encoder,DenseEncoder):
            with self.assertRaises(ValueError):cls('u',tile_size=0)
            with self.assertRaises(ValueError):cls('u',strategy='no')

if __name__=='__main__':unittest.main(verbosity=2)
