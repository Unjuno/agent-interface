import unittest
import numpy as np
from tile_transport import Encoder, Decoder, Frame, packet


class TransportTest(unittest.TestCase):
    def test_exact_changes_edges_modes_and_resizes(self):
        rng = np.random.default_rng(65539)
        for mode, channels in (("L",1),("RGB",3),("RGBA",4)):
            for strategy in ("O1","O2"):
                enc, dec = Encoder("s",strategy,16), Decoder("s")
                for w,h in ((35,29),(17,9)):
                    raw = rng.integers(0,256,(h,w,channels),dtype=np.uint8)
                    frames = [raw.copy(),raw.copy()]
                    for y,x in ((0,0),(h-1,w-1),(16 if h>16 else 0,16)):
                        raw[y,x,0] ^= 1
                        frames.append(raw.copy())
                    frames.append(rng.integers(0,256,(h,w,channels),dtype=np.uint8))
                    for i,a in enumerate(frames):
                        f = Frame(w,h,mode,a.tobytes())
                        self.assertEqual(dec.accept(enc.encode(f,action_id=str(i),observed_ns=i)),f)

    def test_gap_reorder_reconnect_and_atomic_failure(self):
        enc, dec = Encoder("s"), Decoder("s")
        f = Frame(65,65,"RGB",bytes(65*65*3))
        p1 = enc.encode(f,action_id="a",observed_ns=1)
        p2 = enc.encode(f,action_id="b",observed_ns=2)
        with self.assertRaises(ValueError): dec.accept(p2)
        self.assertEqual(dec.sequence,0)
        dec.accept(p1)
        with self.assertRaises(ValueError): dec.accept(p1)
        with self.assertRaises(ValueError): Decoder("other").accept(p1)
        bad = dict(dec.metadata,sequence=2,base=1,kind="tiles",count=1)
        with self.assertRaises(Exception): dec.accept(packet(bad,b"bad"))
        self.assertEqual(dec.sequence,1)
        self.assertEqual(dec.frame,f)
        for count in (-1,0,1.5,True):
            with self.assertRaises(ValueError):
                dec.accept(packet(dict(bad,count=count),b""))
        with self.assertRaises(ValueError): dec.accept(p2+b"trailing")
        self.assertEqual(dec.sequence,1)
        self.assertEqual(dec.accept(p2),f)
        new = Encoder("new").encode(f,action_id="c",observed_ns=3)
        self.assertEqual(Decoder("new").accept(new),f)

    def test_wire_fallback_and_sparse_tiles(self):
        rng = np.random.default_rng(91)
        a = rng.integers(0,256,(128,128,3),dtype=np.uint8)
        o1,o2 = Encoder("s","O1"),Encoder("s","O2")
        dec = Decoder("s")
        kinds=[]
        for i in range(3):
            if i: a[0,0,0] ^= 1
            frame = Frame(128,128,"RGB",a.tobytes())
            args=dict(action_id=str(i),observed_ns=i)
            baseline=o1.encode(frame,**args); delta=o2.encode(frame,**args)
            self.assertLessEqual(len(delta),len(baseline))
            self.assertEqual(dec.accept(delta),frame)
            kinds.append(o2.last["kind"])
        self.assertEqual(kinds,["full","tiles","tiles"])


if __name__ == "__main__": unittest.main()
