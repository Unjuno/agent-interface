"""Verify/unpack UTF-8 evidence without executing any contained program."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import lzma


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    here=Path(__file__).resolve().parent
    meta=json.loads((here/'EVIDENCE.json').read_text())
    compressed=b''
    for part in meta['parts']:
        raw=(here/part['name']).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=part['sha256']:raise ValueError('part hash')
        compressed+=raw
    if hashlib.sha256(compressed).hexdigest()!=meta['compressed_sha256']:raise ValueError('compressed hash')
    obj=lzma.LZMADecompressor(memlimit=256_000_000);raw=obj.decompress(compressed,max_length=10_000_001)
    if len(raw)>10_000_000 or not obj.eof or obj.unused_data:raise ValueError('archive bound/framing')
    if hashlib.sha256(raw).hexdigest()!=meta['decoded_sha256']:raise ValueError('decoded hash')
    files=json.loads(raw)
    if len(files)!=meta['members']:raise ValueError('member inventory')
    checked=[]
    for name,text in files.items():
        path=PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or not path.parts:raise ValueError('member path')
        data=text.encode('utf-8')
        if name in meta['frozen_sources'] and hashlib.sha256(data).hexdigest()!=meta['frozen_sources'][name]:raise ValueError('source hash '+name)
        checked.append((path,data))
    a.out.mkdir(parents=True,exist_ok=False)
    for path,data in checked:
        dest=a.out/path;dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('xb') as f:f.write(data)
    print(json.dumps({'files':len(checked),'decoded_sha256':meta['decoded_sha256'],'executed':False},sort_keys=True))


if __name__=='__main__':
    main()
