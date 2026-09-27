"""Packaging controls only. No GUI, clock calibration, or scientific runner."""
import copy,io,json,shutil,tarfile,tempfile,unittest
from pathlib import Path
from unpack import restore,decode_tar,decode_rows,safe_name
HERE=Path(__file__).resolve().parent

def tar_bytes(entries):
    buf=io.BytesIO()
    with tarfile.open(fileobj=buf,mode='w') as t:
        for name,kind in entries:
            m=tarfile.TarInfo(name);m.type=kind;m.size=0;t.addfile(m,io.BytesIO())
    return buf.getvalue()

class PackagingTests(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(restore(HERE,Path(tmp)/'out')['restored_files'],81)
    def test_existing_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):restore(HERE,Path(tmp))
    def test_paths(self):
        for p in ('../x','/x','a/../x','a//x','a\\x','./x',''):
            with self.subTest(path=p),self.assertRaises(ValueError):safe_name(p)
    def test_duplicate_tar(self):
        with self.assertRaises(ValueError):decode_tar(tar_bytes([('x',tarfile.REGTYPE)]*2),2)
    def test_link_tar(self):
        with self.assertRaises(ValueError):decode_tar(tar_bytes([('x',tarfile.SYMTYPE)]),1)
    def test_wrong_count(self):
        with self.assertRaises(ValueError):decode_tar(tar_bytes([('x',tarfile.REGTYPE)]),2)
    def test_bad_columns(self):
        c={'rows':1,'columns':[[[],[['V',0]]],[[],[['V',0]]]]}
        with self.assertRaises(ValueError):decode_rows(json.dumps(c).encode())
    def test_column_length(self):
        c={'rows':2,'columns':[[[],[['V',0]]]]}
        with self.assertRaises(ValueError):decode_rows(json.dumps(c).encode())
    def bad_publication(self,kind):
        with tempfile.TemporaryDirectory() as tmp:
            pub=Path(tmp)/'pub';pub.mkdir()
            shutil.copy2(HERE/'CAPSULE.json',pub/'CAPSULE.json')
            shutil.copytree(HERE/'capsule',pub/'capsule')
            meta=json.loads((pub/'CAPSULE.json').read_text())
            p=pub/meta['parts'][0]['path']
            if kind=='bytes':
                b=p.read_bytes();p.write_bytes(bytes([b[0]^1])+b[1:])
            elif kind=='missing':p.unlink()
            elif kind=='identity':meta['archive_sha256']='0'*64
            elif kind=='duplicate':meta['parts'].append(meta['parts'][0])
            (pub/'CAPSULE.json').write_text(json.dumps(meta))
            out=Path(tmp)/'out'
            with self.assertRaises(ValueError):restore(pub,out)
            self.assertFalse(out.exists())
    def test_part_bytes(self):self.bad_publication('bytes')
    def test_missing_part(self):self.bad_publication('missing')
    def test_archive_identity(self):self.bad_publication('identity')
    def test_duplicate_part(self):self.bad_publication('duplicate')

if __name__=='__main__':unittest.main(verbosity=2)
