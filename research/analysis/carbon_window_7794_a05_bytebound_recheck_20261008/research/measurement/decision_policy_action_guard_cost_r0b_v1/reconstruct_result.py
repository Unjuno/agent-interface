import argparse,gzip,hashlib,json
from pathlib import Path
p=Path(__file__).parent
m=json.loads((p/'RESULT_MANIFEST.json').read_text())
ap=argparse.ArgumentParser(description='Verify an externally retained #1179 raw result or gzip artifact against the repository commitment.')
ap.add_argument('artifact',type=Path)
a=ap.parse_args()
b=a.artifact.read_bytes()
if hashlib.sha256(b).hexdigest()==m['raw_sha256'] and len(b)==m['raw_bytes']:
    print(m['raw_sha256']);raise SystemExit(0)
if hashlib.sha256(b).hexdigest()==m['gzip_sha256'] and len(b)==m['gzip_bytes']:
    raw=gzip.decompress(b)
    assert len(raw)==m['raw_bytes'] and hashlib.sha256(raw).hexdigest()==m['raw_sha256']
    print(m['raw_sha256']);raise SystemExit(0)
raise SystemExit('artifact does not match frozen raw/gzip commitment')
