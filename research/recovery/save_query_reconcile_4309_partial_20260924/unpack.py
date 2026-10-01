"""Restore lossless UTF-8 research evidence only; never run restored code."""
import argparse,base64,hashlib,json,lzma
from pathlib import Path,PurePosixPath

def unique(pairs):
    out={}
    for k,v in pairs:
        if k in out: raise ValueError('duplicate key')
        out[k]=v
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('manifest',type=Path);p.add_argument('destination',type=Path);a=p.parse_args()
    m=json.loads(a.manifest.read_text(),object_pairs_hook=unique)
    if m['format']!='xz-json-utf8-map-v1': raise ValueError('format')
    parts=m.get('parts',[dict(name=m.get('part'),sha256=m.get('part_sha256'))])
    text=b''
    for part in parts:
        name=PurePosixPath(part['name'])
        if name.is_absolute() or '..' in name.parts: raise ValueError('part path')
        raw=(a.manifest.parent/str(name)).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=part['sha256']: raise ValueError('part hash')
        text+=raw.strip()
    archive=base64.b64decode(text,validate=True)
    if len(archive)!=m['archive_bytes'] or hashlib.sha256(archive).hexdigest()!=m['archive_sha256']: raise ValueError('archive identity')
    if not 0<m['expanded_json_bytes']<=8000000: raise ValueError('expansion bound')
    dec=lzma.LZMADecompressor(memlimit=128*1024*1024)
    data=dec.decompress(archive,max_length=m['expanded_json_bytes']+1)
    if not dec.eof or dec.unused_data or len(data)!=m['expanded_json_bytes']: raise ValueError('expansion length')
    files=json.loads(data,object_pairs_hook=unique)
    if set(files)!=set(m['files']) or len(files)>2000: raise ValueError('inventory')
    for name,s in files.items():
        path=PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or '\\' in name or not name or not isinstance(s,str): raise ValueError('file path/type')
        b=s.encode('utf-8');meta=m['files'][name]
        if len(b)!=meta['bytes'] or hashlib.sha256(b).hexdigest()!=meta['sha256']: raise ValueError('member identity:'+name)
    # Destination must be new under a caller-trusted parent, with no concurrent writers.
    a.destination.mkdir(parents=False,exist_ok=False)
    for name,s in files.items():
        target=a.destination/name;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('x',encoding='utf-8',newline='') as f:f.write(s)
    print(json.dumps(dict(restored=len(files),archive_sha256=m['archive_sha256'],code_executed=False)))
if __name__=='__main__': main()
