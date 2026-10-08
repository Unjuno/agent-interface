"""Verify retained bytes and replay audits only. Never launch a GUI allocation."""
import hashlib, json, lzma, shutil, subprocess, sys, tempfile
from pathlib import Path, PurePosixPath

def restore(data_dir, destination):
    data_dir=Path(data_dir);destination=Path(destination)
    if destination.exists(): raise FileExistsError('new output directory required')
    manifest=json.loads((data_dir/'DATA_MANIFEST.json').read_text())
    parts=[]
    for part in manifest['parts']:
        raw=(data_dir/part['path']).read_bytes()
        if len(raw)!=part['bytes'] or hashlib.sha256(raw).hexdigest()!=part['sha256']:
            raise ValueError('part integrity mismatch')
        parts.append(raw)
    decoder=lzma.LZMADecompressor(memlimit=128*1024*1024)
    raw=decoder.decompress(b''.join(parts),max_length=manifest['raw_json_bytes']+1)
    if not decoder.eof or decoder.unused_data or len(raw)!=manifest['raw_json_bytes']:
        raise ValueError('archive extent mismatch')
    if hashlib.sha256(raw).hexdigest()!=manifest['raw_json_sha256']:
        raise ValueError('archive digest mismatch')
    files=json.loads(raw)
    if type(files) is not dict or len(files)!=manifest['file_count']:
        raise ValueError('member count mismatch')
    if sum(len(value.encode('utf-8')) for value in files.values())!=manifest['member_bytes']:
        raise ValueError('member byte count mismatch')
    for name,value in files.items():
        rel=PurePosixPath(name)
        if not isinstance(value,str) or rel.is_absolute() or '..' in rel.parts or str(rel)!=name:
            raise ValueError('invalid regular member')
    destination.mkdir(parents=True)
    for name,value in files.items():
        path=destination/name;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as out:out.write(value.encode('utf-8'))
    return manifest

def verify(root):
    root=Path(root).resolve()
    with tempfile.TemporaryDirectory(prefix='k8n4-readonly-') as temp:
        dest=Path(temp)/'study'
        manifest=restore(root,dest)
        for name in ('study','current_source'):
            shutil.copytree(root/name,dest/name)
        for name in ('FREEZE.json','PLAN.md','ENVIRONMENT.json','SOURCE_BLOBS.json'):
            shutil.copyfile(root/name,dest/name)
        subprocess.run([sys.executable,'-B',str(dest/'study/prepare.py'),str(dest)],check=True,capture_output=True)
        results={}
        for label,script in [('AUDIT','audit.py'),('CONTROLS','controls.py')]:
            completed=subprocess.run([sys.executable,'-B',str(dest/'study'/script),str(dest)],capture_output=True,check=True)
            if completed.stdout!=(dest/(label+'.json')).read_bytes():raise ValueError(label+' reproduction differs')
            results[label]={'byte_exact':True,'exit':completed.returncode}
        print(json.dumps({'status':'PASS_RETAINED_RECONSTRUCTION','files':manifest['file_count'],
                          'audits':results,'new_gui_runs':0,'nonauthor_review':False},indent=2,sort_keys=True))
if __name__=='__main__': verify(Path(__file__).resolve().parent)
