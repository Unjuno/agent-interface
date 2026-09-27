"""Packaging-only corruptions; no GUI, candidate or allocation runner."""
import base64, hashlib, io, json, lzma, tarfile, tempfile, unittest
from pathlib import Path
import verify_publication as v

class PackagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=json.loads((v.ROOT/'EVIDENCE_MANIFEST.json').read_text())
        z=b''.join(base64.b64decode((v.ROOT/p['path']).read_bytes()) for p in cls.m['parts'])
        with tarfile.open(fileobj=io.BytesIO(lzma.decompress(z))) as t:
            cls.stored={x.name:t.extractfile(x).read() for x in t}

    def bad(self, mutate=None, part_corrupt=False, truncate=False):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); d=dict(self.stored)
            if mutate: mutate(d)
            b=io.BytesIO()
            with tarfile.open(fileobj=b,mode='w',format=tarfile.USTAR_FORMAT) as t:
                for name,raw in d.items():
                    info=tarfile.TarInfo(name);info.size=len(raw);t.addfile(info,io.BytesIO(raw))
            z=lzma.compress(b.getvalue(),preset=1)
            if truncate:z=z[:-8]
            text=base64.b64encode(z)+b'\n';(root/'part.b64').write_bytes(text)
            m=dict(self.m);m.update(archive_bytes=len(z),archive_sha256=v.sha(z),decoded_bytes=len(b.getvalue()),parts=[dict(path='part.b64',size=len(text),sha256=v.sha(text))])
            (root/'EVIDENCE_MANIFEST.json').write_text(json.dumps(m))
            if part_corrupt:(root/'part.b64').write_bytes(b'A'+text[1:])
            with self.assertRaises((ValueError,KeyError,TypeError,lzma.LZMAError)):
                v.restore(root,root/'out')
            self.assertFalse((root/'out').exists())

    def index_mutation(self,fn):
        def change(d):
            i=json.loads(d['INDEX.json']);fn(i);d['INDEX.json']=json.dumps(i).encode()
        return change

    def test_existing_destination(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(FileExistsError):v.restore(v.ROOT,td)
    def test_part_corruption(self):self.bad(part_corrupt=True)
    def test_truncated_xz(self):self.bad(truncate=True)
    def test_traversal(self):self.bad(self.index_mutation(lambda i:i['files'][0].update(path='../escape')))
    def test_duplicate_output(self):self.bad(self.index_mutation(lambda i:i['files'][1].update(path=i['files'][0]['path'])))
    def test_digest(self):self.bad(self.index_mutation(lambda i:i['files'][0].update(sha256='0'*64)))
    def test_stored_type(self):self.bad(self.index_mutation(lambda i:i['files'][0].update(kind='execute')))
    def test_column_length(self):
        def change(d):
            i=json.loads(d['INDEX.json']);e=next(e for e in i['files'] if e['kind']=='jsonl_columns')
            x=json.loads(d[e['stored']]);x['columns'][0][1].pop();d[e['stored']]=json.dumps(x).encode()
        self.bad(change)

if __name__=='__main__':unittest.main()
