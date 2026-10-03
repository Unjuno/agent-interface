"""Pure PNG/capture connection regressions; no WinDLL or actual input/capture."""
from pathlib import Path
import hashlib,struct,tempfile,unittest,zlib
from . import backend as native
from .capture_artifacts import CaptureArtifacts

def decode_png(path):
    data=path.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n';pos=8;payload=b'';header=None;types=[]
    while pos<len(data):
        size=struct.unpack('>I',data[pos:pos+4])[0];kind=data[pos+4:pos+8];chunk=data[pos+8:pos+8+size];crc=struct.unpack('>I',data[pos+8+size:pos+12+size])[0]
        assert zlib.crc32(kind+chunk)&0xffffffff==crc
        types.append(kind)
        if kind==b'IHDR':header=struct.unpack('>IIBBBBB',chunk)
        if kind==b'IDAT':payload+=chunk
        pos+=size+12
    assert pos==len(data) and types==[b'IHDR',b'IDAT',b'IEND'] and header[2:]==(8,2,0,0,0)
    raw=zlib.decompress(payload);w,h=header[:2];assert len(raw)==h*(w*3+1)
    pixels=b''
    for y in range(h):
        row=raw[y*(w*3+1):(y+1)*(w*3+1)];assert row[0]==0;pixels+=row[1:]
    return w,h,pixels

class PNGConnectionTests(unittest.TestCase):
    def setUp(self):
        self.b=native.Win32Backend.__new__(native.Win32Backend);self.calls=[]
        self.raw=bytes([0,0,255,7,0,255,0,11,255,0,0,19,255,255,255,23])
        self.b._capture_hdc=lambda *a,**kw:self.calls.append([list(a),kw]) or self.raw
        self.directory=Path(self.enterContext(tempfile.TemporaryDirectory()))
    def configure(self):
        method=getattr(self.b,'configure_capture_artifacts',None);self.assertTrue(callable(method),'Win32 PNG artifact connection missing');method(self.directory)
    def test_same_capture_pixels_and_current_metadata(self):
        self.configure();row=self.b.capture('owned','screen_physical_px',0,0,2,2)
        self.assertEqual(len(self.calls),1);self.assertEqual(row['sha256'],hashlib.sha256(self.raw).hexdigest())
        self.assertEqual(decode_png(Path(row['artifact']['path'])),(2,2,bytes([255,0,0,0,255,0,0,0,255,255,255,255])))
        self.assertEqual(row['artifact']['source_raw_sha256'],row['sha256']);self.assertLessEqual(row['capture_started_ns'],row['capture_ended_ns'])
        self.assertEqual(row['region'],[0,0,2,2]);self.assertEqual(row['target'],'owned')
    def test_equal_pixels_have_distinct_saved_identity(self):
        self.configure();a=self.b.capture('owned','screen_physical_px',0,0,2,2);b=self.b.capture('owned','screen_physical_px',0,0,2,2)
        self.assertEqual(len(self.calls),2);self.assertNotEqual(a['artifact']['path'],b['artifact']['path']);self.assertEqual(a['artifact']['sha256'],b['artifact']['sha256'])
    def test_writer_failure_retains_original_capture(self):
        self.configure()
        def failed(*args,**kwargs):raise OSError('inert disk failure')
        self.b.capture_artifacts.write=failed
        row=self.b.capture('owned','screen_physical_px',0,0,2,2)
        self.assertEqual(len(self.calls),1);self.assertEqual(row['sha256'],hashlib.sha256(self.raw).hexdigest());self.assertIn('inert disk failure',row['artifact_error']);self.assertNotIn('artifact',row)
    def test_metadata_only_keeps_original_shape(self):
        row=self.b.capture('owned','screen_physical_px',0,0,2,2)
        self.assertEqual(set(row),{'bytes','sha256','width','height'});self.assertEqual(len(self.calls),1)

class BoundaryTests(unittest.TestCase):
    def test_client_crop_is_encoded_without_recapture(self):
        b=native.Win32Backend.__new__(native.Win32Backend);calls=[]
        b._target=lambda name:17;b.geometry=lambda name:dict(width=3,height=2)
        raw=bytes([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24])
        b._capture_hdc=lambda *a,**kw:calls.append([a,kw]) or raw
        directory=Path(self.enterContext(tempfile.TemporaryDirectory()))
        b.configure_capture_artifacts(directory)
        result=b.capture('owned','window_client',1,1,2,1)
        self.assertEqual(calls,[[(17,0,0,3,2),{'print_window':True}]])
        self.assertEqual(result['sha256'],hashlib.sha256(raw[16:24]).hexdigest())
        self.assertEqual(decode_png(Path(result['artifact']['path'])),(2,1,bytes([19,18,17,23,22,21])))
    def test_malformed_pixel_images_never_create_artifacts(self):
        directory=Path(self.enterContext(tempfile.TemporaryDirectory()))
        writer=CaptureArtifacts(directory);before=set(directory.iterdir())
        for raw,w,h in [(b'\0'*4,True,1),(b'\0'*4,1,False),(b'\0'*3,1,1),(b'\0'*5,1,1),(bytearray(4),1,1),(b'',0,1),(b'',8193,1),(b'',8192,8192)]:
            with self.subTest(w=w,h=h,length=len(raw)):
                with self.assertRaises(ValueError):writer.write(raw,w,h)
        self.assertEqual(set(directory.iterdir()),before)

if __name__=='__main__':unittest.main(verbosity=2)
