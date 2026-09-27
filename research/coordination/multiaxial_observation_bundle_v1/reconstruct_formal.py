from __future__ import annotations
import argparse, base64, gzip, hashlib, pathlib
EXPECTED = "ebc8d23640d80516e85f1d6c2e6cabd85d107e9c8b19eade5fc8f85a5d092293"

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out', required=True); args=ap.parse_args()
    root=pathlib.Path(__file__).resolve().parent
    raw=gzip.decompress(base64.b64decode((root/'formal.json.gz.b64').read_text()))
    got=hashlib.sha256(raw).hexdigest()
    if got != EXPECTED: raise SystemExit(f'SHA256 mismatch: {got}')
    out=pathlib.Path(args.out)
    if out.exists(): raise SystemExit('output exists')
    out.write_bytes(raw)
    print(f'PASS_RECONSTRUCT {got} {len(raw)} bytes')
if __name__=='__main__': main()
