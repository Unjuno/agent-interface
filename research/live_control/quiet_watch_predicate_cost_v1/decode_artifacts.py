#!/usr/bin/env python3
import argparse, base64, gzip, hashlib
from pathlib import Path

def decode(src, dst, expected_sha256):
    raw=gzip.decompress(base64.b64decode(Path(src).read_bytes()))
    got=hashlib.sha256(raw).hexdigest()
    if got != expected_sha256:
        raise SystemExit(f'{src}: SHA-256 mismatch {got} != {expected_sha256}')
    Path(dst).write_bytes(raw)
    print(f'{dst}: {len(raw)} bytes sha256={got}')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--dir',default='.'); a=ap.parse_args(); d=Path(a.dir)
    decode(d/'result.json.gz.b64', d/'result.json', '5fecb9db505c3b82816d571ba7b96c9b4445d350f41efc7c7283dfe4dc9a3b8a')
    decode(d/'native_predicate.so.gz.b64', d/'native_predicate.cpython-313-x86_64-linux-gnu.so', 'fb091f2997882c664e740d90c8f5f1c8a8f64d86410ede851a08105aa01e1d3d')
if __name__=='__main__': main()
