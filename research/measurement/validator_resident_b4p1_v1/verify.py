"""Reconstruct retained bytes and audit; never rerun timing workers."""
import base64
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import tempfile
ROOT=Path(__file__).resolve().parent


def digest(data):return hashlib.sha256(data).hexdigest()


def main():
    meta=json.loads((ROOT/'CAPSULE.json').read_text())
    chunks=[]
    for part in meta['parts']:
        data=(ROOT/'capsule'/part['name']).read_bytes()
        assert len(data)==part['bytes'] and digest(data)==part['sha256']
        chunks.append(data.strip())
    packed=base64.b64decode(b''.join(chunks),validate=True)
    assert len(packed)==meta['bytes'] and digest(packed)==meta['sha256']
    decompressor=lzma.LZMADecompressor(memlimit=134217728)
    data=decompressor.decompress(packed,max_length=2000001)
    assert len(data)<=2000000 and decompressor.eof and not decompressor.unused_data
    with tempfile.TemporaryDirectory(prefix='b4p1-readonly-') as name:
        dest=Path(name);seen=set();total=0
        with tarfile.open(fileobj=io.BytesIO(data),mode='r:') as archive:
            for member in archive:
                path=PurePosixPath(member.name)
                assert member.isfile() and not path.is_absolute() and '..' not in path.parts
                assert member.name not in seen and 0<=member.size<=1000000
                seen.add(member.name);total+=member.size
                assert total<=meta['member_bytes']
                out=dest.joinpath(*path.parts);out.parent.mkdir(parents=True,exist_ok=True)
                out.write_bytes(archive.extractfile(member).read())
        assert len(seen)==meta['members'] and total==meta['member_bytes']
        manifest=json.loads((dest/'MANIFEST.json').read_text())
        assert seen==set(manifest)|{'MANIFEST.json'}
        for path,spec in manifest.items():
            b=(dest/path).read_bytes();assert len(b)==spec['bytes'] and digest(b)==spec['sha256']
        freeze=json.loads((dest/'FREEZE.json').read_text())
        for path in list(freeze)+['FREEZE.json']:
            assert (ROOT/path).read_bytes()==(dest/path).read_bytes(),path
        checks=[(['audit.py',str(dest/'measured')],'AUDIT.json',0),
                (['controls.py',str(dest/'measured')],'CONTROLS.json',0),
                (['audit.py',str(dest/'construction01'),'--construction'],'construction01/FAILED_AUDIT.json',1),
                (['audit.py',str(dest/'construction02'),'--construction'],'CONSTRUCTION_AUDIT.json',0),
                (['controls.py',str(dest/'construction02'),'--construction'],'CONSTRUCTION_CONTROLS.json',0)]
        for args,output,code in checks:
            cmd=[sys.executable,'-I','-S','-B',str(dest/args[0])]+args[1:]
            p=subprocess.run(cmd,capture_output=True,timeout=15)
            assert p.returncode==code and not p.stderr,(args,p.returncode,p.stderr)
            assert p.stdout==(dest/output).read_bytes(),output
        result=json.loads((dest/'RESULT.json').read_text())
        print(json.dumps(dict(decision='PASS_READONLY_RECONSTRUCTION',members=len(seen),member_bytes=total,source_files=18,audit_checks=result['audit_checks'],measured_responses=result['responses'],measured_processes=result['processes'],controls_reproduced=16,original_construction_fail_preserved=True,benchmark_reruns=0),sort_keys=True))


if __name__=='__main__':main()
