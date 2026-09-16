#!/usr/bin/env python3
import gzip,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
p=HERE/'compact-results.json.gz';gz=p.read_bytes();assert hashlib.sha256(gz).hexdigest()=='d3dd2a5bf15dd8a7f0fbb47ce1de9f7e9ba35765626379b3cdbb4ef60558d358'
raw=gzip.decompress(gz);assert hashlib.sha256(raw).hexdigest()=='07375b613b1d6eee3fa818d734d7f535ab54f08cc4d0e8f0ff30cb28822bea01'
obj=json.loads(raw);assert len(obj['results'])==12 and obj['audit']['decision']=='PASS_INKSCAPE_XI2_PINCH_TRANSFER_SCOPED' and obj['postformal']['pass'] is True and obj['controls']['pass'] is True
(HERE/'compact-results.reconstructed.json').write_bytes(raw)
print(json.dumps({'gzip_sha256':hashlib.sha256(gz).hexdigest(),'raw_sha256':hashlib.sha256(raw).hexdigest(),'results':len(obj['results']),'decision':obj['audit']['decision']},sort_keys=True))
