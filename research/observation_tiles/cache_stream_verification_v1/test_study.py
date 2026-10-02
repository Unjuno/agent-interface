"""Excluded construction: content, resource bounds, and PNG/source checks."""
import hashlib,io,tempfile,unittest
from pathlib import Path
from PIL import Image
from stream_guard import GuardedSink,inspect_bytes,CHUNK_BYTES,MAX_ENCODED_BYTES
from legacy_candidate import Candidate
from vendor.exact_gate import Frame
from png_oracle import decode

class Tests(unittest.TestCase):
    def test_incremental_digest_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'data'
            for n in (1,65535,65536,65537,262144,262145):
                data=hashlib.shake_256(str(n).encode()).digest(n);path.write_bytes(data)
                for mode in ('FULL_PIN','STREAM_PIN'):
                    r=inspect_bytes(path,n,hashlib.sha256(data).hexdigest(),mode,trace=True)
                    self.assertEqual(r['status'],'MATCH');self.assertEqual(r['hash_bytes'],n)
                    self.assertEqual(r['read_bytes'],n)
                    if mode=='STREAM_PIN':self.assertLessEqual(r['max_request_bytes'],CHUNK_BYTES)
    def test_changed_tail(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'data';data=b'x'*300000;path.write_bytes(data[:-1]+b'y')
            for mode in ('FULL_PIN','STREAM_PIN'):
                r=inspect_bytes(path,len(data),hashlib.sha256(data).hexdigest(),mode)
                self.assertEqual(r['status'],'DIGEST_MISMATCH');self.assertEqual(r['hash_bytes'],len(data))
    def test_missing_and_length(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'x'
            for mode in ('FULL_PIN','STREAM_PIN'):
                self.assertEqual(inspect_bytes(p,5,'0'*64,mode)['status'],'UNAVAILABLE')
            p.write_bytes(b'xx')
            for mode in ('FULL_PIN','STREAM_PIN'):
                r=inspect_bytes(p,5,'0'*64,mode);self.assertEqual(r['status'],'LENGTH_MISMATCH');self.assertEqual(r['read_bytes'],0)
    def test_absolute_and_type_bounds(self):
        for n in (0,-1,True,MAX_ENCODED_BYTES+1):
            r=inspect_bytes(Path('/not-used'),n,None,'STREAM_PIN');self.assertEqual(r['status'],'UNSUPPORTED_SIZE');self.assertEqual(r['read_calls'],0)
    def test_small_reuse(self):
        frame=Frame(40,30,'RGB',b'\x01\x02\x03'*(40*30))
        for mode in ('FULL_PIN','STREAM_PIN'):
            with tempfile.TemporaryDirectory() as d:
                s=GuardedSink(Path(d),mode);a=s.publish(frame);b=s.publish(frame)
                self.assertFalse(a['receipt']['image_reused']);self.assertTrue(b['receipt']['image_reused'])
                self.assertEqual(b['guard']['status'],'MATCH')
    def test_large_reuse_and_repair(self):
        frame=Frame(384,320,'RGB',hashlib.shake_256(b'excluded-construction').digest(384*320*3))
        for mode in ('FULL_PIN','STREAM_PIN'):
            with tempfile.TemporaryDirectory() as d:
                s=GuardedSink(Path(d),mode);a=s.publish(frame);self.assertGreater(s.length,262144)
                self.assertTrue(s.publish(frame)['receipt']['image_reused'])
                p=s.sink.path;p.write_bytes(p.read_bytes()[:-32]+b'Y'*32)
                b=s.publish(frame);self.assertFalse(b['receipt']['image_reused'])
                self.assertEqual(b['guard']['status'],'DIGEST_MISMATCH')
                self.assertTrue(s.publish(frame)['receipt']['image_reused'])
                self.assertEqual(decode(s.sink.path.read_bytes())[2],frame.pixels)
    def test_legacy_size_boundary(self):
        frame=Frame(384,320,'RGB',hashlib.shake_256(b'excluded-construction').digest(384*320*3))
        with tempfile.TemporaryDirectory() as d:
            s=Candidate(d,'BYTE_PIN_REPAIR');s.publish(frame)
            self.assertFalse(s.publish(frame)['receipt']['image_reused'])
    def test_collision_preserved(self):
        for mode in ('FULL_PIN','STREAM_PIN'):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d);s=GuardedSink(p,mode)
                s.publish(Frame(1,1,'RGB',b'abc'));(p/'002.png').write_bytes(b'sentinel')
                with self.assertRaises(FileExistsError):s.publish(Frame(1,1,'RGB',b'def'))
                self.assertEqual((p/'002.png').read_bytes(),b'sentinel')
    def test_decoder_matches_and_rejects_crc(self):
        pixels=hashlib.shake_256(b'decoder-construction').digest(13*11*3)
        buf=io.BytesIO();Image.frombytes('RGB',(13,11),pixels).save(buf,format='PNG')
        raw=buf.getvalue();self.assertEqual(decode(raw),(13,11,pixels))
        altered=bytearray(raw);altered[-5]^=1
        with self.assertRaises(ValueError):decode(bytes(altered))
    def test_length_probe_does_not_mutate(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'data';b=b'correct immutable bytes';p.write_bytes(b)
            for mode in ('FULL_PIN','STREAM_PIN'):
                r=inspect_bytes(p,len(b),hashlib.sha256(b).hexdigest(),mode,trace=True)
                self.assertEqual(r['status'],'MATCH');self.assertEqual(p.read_bytes(),b)

if __name__=='__main__':unittest.main(verbosity=2)
