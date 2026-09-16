#!/usr/bin/env python3
from pathlib import Path
import gzip,hashlib,json,sys
p=Path(sys.argv[1] if len(sys.argv)>1 else 'compact-results.json.gz'); raw=gzip.decompress(p.read_bytes()); want='0c68b054e01029199645eb347ec745e483b921bdb9ab3df85e46e444ad4f6216'
pub=p.with_name('publication.json')
if pub.exists(): want=json.loads(pub.read_text())['compact_raw_sha256']
assert hashlib.sha256(raw).hexdigest()==want
out=p.with_suffix('').with_suffix('.reconstructed.json');out.write_bytes(raw);print(json.dumps({'bytes':len(raw),'sha256':want,'output':str(out)},sort_keys=True))
