import base64,gzip,hashlib,pathlib
b=base64.b64decode(pathlib.Path("RAW.json.gz.b64").read_bytes())
r=gzip.decompress(b)
exp="71e9a44f02e86d498c567cd4286f6171e8472dee9e469fce7a7716b345d4f468"
assert hashlib.sha256(r).hexdigest()==exp
pathlib.Path("RAW.restored.json").write_bytes(r)
print(exp)
