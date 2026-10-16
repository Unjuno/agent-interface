#!/usr/bin/env python3
from pathlib import Path
import gzip,hashlib,json,sys
p=Path(sys.argv[1] if len(sys.argv)>1 else "compact-results.json.gz")
raw=gzip.decompress(p.read_bytes())
want="264819814006c1292b3e3f43d8752dd190ac9ab3960917876f0c386bce724ce9"
assert hashlib.sha256(raw).hexdigest()==want
out=p.with_suffix("").with_suffix(".reconstructed.json")
out.write_bytes(raw)
print(json.dumps({"bytes":len(raw),"sha256":want,"output":str(out)},sort_keys=True))
