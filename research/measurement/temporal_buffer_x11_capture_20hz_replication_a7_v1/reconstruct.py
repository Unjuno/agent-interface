#!/usr/bin/env python3
"""Decode retained sources/aggregate results only. Never run the formal experiment."""
import argparse
import base64
import hashlib
import io
import json
import lzma
import tarfile
from pathlib import Path


def safe_path(root, name):
    path=Path(name)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('Unsafe archive member')
    return root/path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    here=Path(__file__).resolve().parent
    manifest=json.loads((here/'SOURCE_MANIFEST.json').read_text())
    encoded=''.join((here/name).read_text() for name in manifest['parts'])
    archive=base64.b64decode(''.join(encoded.split()),validate=True)
    if hashlib.sha256(archive).hexdigest()!=manifest['archive_sha256']:
        raise ValueError('Source archive hash mismatch')
    result_bytes=lzma.decompress(base64.b64decode((here/'RESULT_BUNDLE.json.xz.b64').read_text()))
    if hashlib.sha256(result_bytes).hexdigest()!='6f29352829afd3c18d0a882168354626aa04d4b3c537a1e00bbc44b6fc3c7193':
        raise ValueError('Result bundle hash mismatch')
    args.output.mkdir(parents=True,exist_ok=False)
    with tarfile.open(fileobj=io.BytesIO(archive),mode='r:xz') as tar:
        for member in tar.getmembers():
            if not member.isfile():
                raise ValueError('Only regular source files allowed')
            dest=safe_path(args.output,member.name)
            dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open('xb') as f:
                f.write(tar.extractfile(member).read())
    freeze=json.loads((args.output/'FREEZE.json').read_text())
    for name,digest in freeze['sha256'].items():
        if hashlib.sha256(safe_path(args.output,name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Frozen member mismatch: '+name)
    bundle=json.loads(result_bytes)
    for name,text in bundle['files'].items():
        data=text.encode('utf-8')
        if hashlib.sha256(data).hexdigest()!=bundle['sha256'][name]:
            raise ValueError('Result member mismatch: '+name)
        dest=safe_path(args.output,name)
        dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('xb') as f:
            f.write(data)
    print('Verified frozen sources and aggregate result/audits:',args.output)
    print('Full raw/pixel re-audit requires the conversation evidence ZIP. No experiment was rerun.')

if __name__=='__main__':
    main()
