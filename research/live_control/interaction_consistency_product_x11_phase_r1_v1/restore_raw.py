#!/usr/bin/env python3
import base64,gzip,hashlib,json,pathlib,sys
ROOT=pathlib.Path(__file__).parent
b=json.loads((ROOT/'RESULT_BINDING.json').read_text())
s=(ROOT/'RAW_CASES.json.gz.b64').read_bytes()
if hashlib.sha256(s).hexdigest()!=b['raw_b64_sha256']: raise SystemExit('raw_b64_sha256')
gz=base64.b64decode(s)
if hashlib.sha256(gz).hexdigest()!=b['raw_gzip_sha256']: raise SystemExit('raw_gzip_sha256')
raw=gzip.decompress(gz)
if hashlib.sha256(raw).hexdigest()!=b['raw_sha256']: raise SystemExit('raw_sha256')
out=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else ROOT/'RESTORED_RAW_CASES.json');out.write_bytes(raw)
print(json.dumps({'pass':True,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'output':str(out)},sort_keys=True))
