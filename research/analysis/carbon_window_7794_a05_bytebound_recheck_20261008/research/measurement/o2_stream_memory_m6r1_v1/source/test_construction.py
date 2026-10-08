"""Excluded small semantic/rollback checks; no formal timing/allocation."""
import unittest
from unittest.mock import patch
import numpy as np
import stream_encoder as s

class Construction(unittest.TestCase):
    def test_modes_edges_and_state(self):
        for mode,c in [('RGB',3),('RGBA',4),('L',1)]:
            for size in (1,7,32):
                old,new=s.Encoder('c',tile_size=size),s.StreamingEncoder('c',tile_size=size)
                a=np.arange(31*23*c,dtype=np.uint8).reshape(23,31,c)
                frames=[s.Frame(31,23,mode,a.tobytes())]*2
                a[12,15,0]^=1;frames.append(s.Frame(31,23,mode,a.tobytes()))
                a^=255;frames.append(s.Frame(31,23,mode,a.tobytes()))
                frames.append(s.Frame(5,9,mode,bytes(5*9*c)))
                dec=s.Decoder('c')
                for i,f in enumerate(frames):
                    kw=dict(action_id=str(i),observed_ns=i,context=('c',i))
                    before=old.encode(f,**kw);after=new.encode(f,**kw)
                    self.assertEqual(before,after);self.assertEqual(dec.accept(after),f)
                    self.assertEqual((old.previous,old.sequence), (new.previous,new.sequence))
                    self.assertEqual({k:v for k,v in old.last.items() if k!='encode_ns'},
                                     {k:v for k,v in new.last.items() if k!='encode_ns'})
    def test_o1(self):
        old,new=s.Encoder('c','O1'),s.StreamingEncoder('c','O1')
        for i,raw in enumerate([bytes(64),bytes([1])*64,bytes([1])*64]):
            f=s.Frame(8,8,'L',raw);kw=dict(action_id='a',observed_ns=i)
            self.assertEqual(old.encode(f,**kw),new.encode(f,**kw))
    def test_compression_start_rollback(self):
        enc=s.StreamingEncoder('c');f=s.Frame(8,8,'L',bytes(64))
        enc.encode(f,action_id='a',observed_ns=0)
        state=(enc.previous,enc.sequence,enc.last.copy())
        with patch.object(s.zlib,'compressobj',side_effect=RuntimeError('construction only')):
            with self.assertRaises(RuntimeError):
                enc.encode(s.Frame(8,8,'L',bytes([1])*64),action_id='b',observed_ns=1)
        self.assertEqual(state,(enc.previous,enc.sequence,enc.last))
    def test_compression_finish_rollback(self):
        enc=s.StreamingEncoder('c');f=s.Frame(8,8,'L',bytes(64))
        enc.encode(f,action_id='a',observed_ns=0);state=(enc.previous,enc.sequence,enc.last.copy())
        class Failing:
            def compress(self,raw): return b''
            def flush(self,mode): raise RuntimeError('construction only')
        with patch.object(s.zlib,'compressobj',return_value=Failing()):
            with self.assertRaises(RuntimeError):
                enc.encode(s.Frame(8,8,'L',bytes([1])*64),action_id='b',observed_ns=1)
        self.assertEqual(state,(enc.previous,enc.sequence,enc.last))
    def test_metadata_rollback(self):
        enc=s.StreamingEncoder('c')
        with self.assertRaises(TypeError): enc.encode(s.Frame(1,1,'L',b'x'),action_id=object(),observed_ns=0)
        self.assertEqual((enc.previous,enc.sequence,enc.last),(None,0,{}))
    def test_single_pixel_and_full_choice(self):
        rng=np.random.default_rng(623);a=rng.integers(0,256,(80,75,3),dtype=np.uint8)
        old,new=s.Encoder('c',tile_size=16),s.StreamingEncoder('c',tile_size=16)
        f=s.Frame(75,80,'RGB',a.tobytes())
        for enc in (old,new):enc.encode(f,action_id='a',observed_ns=0)
        a[0,0,0]^=1;f=s.Frame(75,80,'RGB',a.tobytes())
        self.assertEqual(old.encode(f,action_id='b',observed_ns=1),new.encode(f,action_id='b',observed_ns=1))
        self.assertEqual(new.last['kind'],'tiles')

if __name__=='__main__':unittest.main(verbosity=2)
