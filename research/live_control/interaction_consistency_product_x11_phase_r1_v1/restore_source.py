#!/usr/bin/env python3
import base64,gzip,hashlib,json,pathlib,sys
ROOT=pathlib.Path(__file__).parent
binding=json.loads((ROOT/'SOURCE_BINDING.json').read_text())
parts=[]
for p in binding['parts']:
 d=(ROOT/p).read_bytes()
 if hashlib.sha256(d).hexdigest()!=binding['part_sha256'][p]: raise SystemExit('part_sha256:'+p)
 parts.append(d)
b64=b''.join(parts)
if hashlib.sha256(b64).hexdigest()!=binding['bundle_b64_sha256']: raise SystemExit('bundle_b64_sha256')
gz=base64.b64decode(b64)
if hashlib.sha256(gz).hexdigest()!=binding['decoded_bundle_gzip_sha256']: raise SystemExit('gzip_sha256')
data=gzip.decompress(gz)
if hashlib.sha256(data).hexdigest()!=binding['decoded_bundle_sha256']: raise SystemExit('decoded_bundle_sha256')
bundle=json.loads(data); freeze=json.loads((ROOT/'FREEZE.json').read_text()); out=ROOT/(sys.argv[1] if len(sys.argv)>1 else 'restored_source'); out.mkdir(parents=True,exist_ok=True); errors=[]
for name,s in bundle['files'].items():
 d=base64.b64decode(s); (out/name).write_bytes(d)
 if hashlib.sha256(d).hexdigest()!=freeze['sha256'][name]:errors.append(name)
print(json.dumps({'pass':not errors,'errors':errors,'files':sorted(bundle['files'])},sort_keys=True));raise SystemExit(bool(errors))
