"""Lossless evidence verification only. Never invokes run.py or GUI input."""
import base64, hashlib, json, lzma, subprocess, sys, tempfile
from pathlib import Path, PurePosixPath

BASE=Path(__file__).resolve().parent

def sha(b): return hashlib.sha256(b).hexdigest()

def main():
    manifest=json.loads((BASE/'EVIDENCE_MANIFEST.json').read_text())
    chunks=[]
    for item in manifest['parts']:
        data=(BASE/item['path']).read_bytes()
        if sha(data)!=item['sha256']: raise ValueError('part digest mismatch: '+item['path'])
        chunks.append(data.strip())
    archive=base64.b64decode(b''.join(chunks),validate=True)
    if sha(archive)!=manifest['archive_sha256']: raise ValueError('archive digest mismatch')
    files=json.loads(lzma.decompress(archive))
    if len(files)!=manifest['file_count']: raise ValueError('archive membership mismatch')
    digests={name:sha(text.encode('utf-8')) for name,text in files.items()}
    with tempfile.TemporaryDirectory(prefix='nested-lineage-audit-') as td:
        root=Path(td)
        for name,text in files.items():
            path=PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts: raise ValueError('unsafe archive path')
            data=text.encode('utf-8')
            if sha(data)!=digests[name]: raise ValueError('file digest mismatch: '+name)
            dest=root/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        freeze=json.loads((root/'FREEZE.json').read_text())
        for name,digest in freeze['sources'].items():
            if sha((BASE/name).read_bytes())!=digest or sha((root/name).read_bytes())!=digest:
                raise ValueError('frozen source differs: '+name)
        for rep in (0,1):
            launch=json.loads((root/f'LAUNCHER{rep}.json').read_text())
            batch=json.loads((root/f'formal/batch-{rep}/BATCH.json').read_text())
            if launch['returncode']!=0 or batch['construction'] is not False or batch['rep']!=rep or batch['status']!='COMPLETE':
                raise ValueError('formal batch/launcher mismatch')
        original_controls=(root/'CONTROLS.json').read_bytes()
        commands=[
            [sys.executable,'-B','audit.py','formal','--reps','0','1','--freeze','FREEZE.json','--out','REAUDIT.json'],
            [sys.executable,'-B','controls.py','formal','0','1'],
            [sys.executable,'-B','-m','unittest','-v','test_policy'],
        ]
        for cmd in commands:
            subprocess.run(cmd,cwd=root,check=True,timeout=20)
        if (root/'REAUDIT.json').read_bytes()!=(root/'AUDIT.json').read_bytes(): raise ValueError('audit not byte-exact')
        if (root/'CONTROLS.json').read_bytes()!=original_controls: raise ValueError('controls not byte-exact')
        for name,digest in digests.items():
            if sha((root/name).read_bytes())!=digest: raise ValueError('retained file changed: '+name)
    print(json.dumps(dict(status='PASS_LOSSLESS_READONLY_RECONSTRUCTION',files=len(files),archive_sha256=sha(archive),gui_runs=0),sort_keys=True))

if __name__=='__main__': main()
