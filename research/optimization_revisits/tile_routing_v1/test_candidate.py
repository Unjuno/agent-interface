"""Differential integration tests against the unchanged repository decoder."""
import json
import random
import unittest
from unittest.mock import patch

import candidate
from candidate import CoverageEncoder
from tile_transport import Decoder, Encoder, Frame, PREFIX


def f(w=129, h=65, mode='RGB', value=0):
    return Frame(w, h, mode, bytes([value]) * w * h * {'RGB':3,'RGBA':4,'L':1}[mode])


def mutate(frame, index, value=1):
    b = bytearray(frame.pixels)
    b[index] = value
    return Frame(frame.width, frame.height, frame.mode, bytes(b))


def push(enc, frame, i=0):
    return enc.encode(frame, action_id=f'action-{i}', observed_ns=i + 1, context=('scope', i))


class Tests(unittest.TestCase):
    def setUp(self):
        self.enc, self.dec = CoverageEncoder('s'), Decoder('s')

    def pair(self, frames):
        for i, frame in enumerate(frames):
            got = self.dec.accept(push(self.enc, frame, i))
            self.assertEqual(got, frame)
            self.assertEqual(self.dec.metadata['context'], ['scope', i])
            self.assertEqual(self.dec.metadata['action_id'], f'action-{i}')
            self.assertEqual(self.dec.metadata['observed_ns'], i + 1)

    def test_initial(self):
        self.pair([f()]); self.assertEqual(self.enc.last['kind'], 'full')

    def test_unchanged_new_context(self):
        self.pair([f(), f()]); self.assertEqual(self.enc.last['kind'], 'unchanged')

    def test_single_channel_edge(self):
        for mode in ('L','RGB','RGBA'):
            for pos in (0, -1):
                frame = f(mode=mode)
                self.pair([frame, mutate(frame,pos)])

    def test_sparse_selects_tiles(self):
        frame = f(640,480)
        self.pair([frame, mutate(frame,-1)])
        self.assertEqual(self.enc.last['kind'],'tiles')

    def test_dense_early_exit(self):
        self.pair([f(640,480), f(640,480,value=1)])
        self.assertEqual(self.enc.last['kind'], 'full')
        self.assertLess(self.enc.last['visited_tiles'],80)

    def test_exact_quarter_uses_tiles(self):
        frame = f(128,128)
        self.pair([frame,mutate(frame,0)])
        self.assertEqual(self.enc.last['kind'],'tiles')

    def test_over_quarter_uses_full(self):
        frame = f(128,128)
        self.pair([frame,mutate(mutate(frame,0),64*3)])
        self.assertEqual(self.enc.last['kind'],'full')

    def test_geometry_mode_reset(self):
        self.pair([f(),f(10,21,'L'),f(10,21,'RGBA'),f(65,129)])
        self.assertEqual(self.enc.last['kind'],'full')

    def test_gap_rejected_atomically(self):
        push(self.enc,f(),0)
        with self.assertRaises(ValueError): self.dec.accept(push(self.enc,f(),1))
        self.assertEqual(self.dec.sequence,0); self.assertIsNone(self.dec.frame)

    def test_cross_stream_rejected(self):
        with self.assertRaises(ValueError): Decoder('other').accept(push(self.enc,f()))

    def test_replay_rejected_atomically(self):
        wire=push(self.enc,f()); self.dec.accept(wire)
        with self.assertRaises(ValueError): self.dec.accept(wire)
        self.assertEqual(self.dec.sequence,1)

    def test_reconnect_full(self):
        self.pair([f(),f()])
        wire=push(CoverageEncoder('new'),f())
        self.assertEqual(Decoder('new').accept(wire),f())

    def test_serialization_failure_atomic(self):
        self.pair([f()])
        with patch.object(candidate,'packet',side_effect=RuntimeError('synthetic serializer failure')):
            with self.assertRaises(RuntimeError): push(self.enc,f(value=1),1)
        self.assertEqual(self.enc.sequence,1); self.assertEqual(self.enc.previous,f())

    def test_one_compression_per_push(self):
        with patch.object(candidate,'packet',wraps=candidate.packet) as spy:
            self.pair([f(),f(),f(value=1),mutate(f(value=1),-1,2)])
            self.assertEqual(spy.call_count,4)

    def test_shared_decoder_mixed_encoders(self):
        encs=[Encoder('s','O1'),Encoder('s','O2'),CoverageEncoder('s')]
        frames=[f(128,128),mutate(f(128,128),0),f(128,128,value=2)]
        for i,(enc,frame) in enumerate(zip(encs,frames)):
            enc.sequence=i; enc.previous=frames[i-1] if i else None
            self.assertEqual(self.dec.accept(push(enc,frame,i)),frame)

    def test_random_differential(self):
        rng=random.Random(990701)
        for mode in ('L','RGB','RGBA'):
            for size in (1,7,64,128):
                enc=CoverageEncoder('random',tile_size=size); dec=Decoder('random')
                old=f(17,19,mode)
                for i in range(12):
                    data=bytearray(old.pixels)
                    for _ in range(i): data[rng.randrange(len(data))]=rng.randrange(256)
                    frame=Frame(17,19,mode,bytes(data))
                    self.assertEqual(dec.accept(push(enc,frame,i)),frame)
                    old=frame


if __name__ == '__main__': unittest.main(verbosity=2)
