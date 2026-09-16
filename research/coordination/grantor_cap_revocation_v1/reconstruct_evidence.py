import base64,hashlib,pathlib,sys
EXPECTED="8998116524231673c2c7fdc1c333e078bb9a8980aeb0257dae03efe20a228dba"
src=pathlib.Path(__file__).with_name("evidence.tar.xz.b64")
out=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "grantor_cap_revocation_v1_evidence.tar.xz")
data=base64.b64decode("".join(src.read_text().split())); h=hashlib.sha256(data).hexdigest()
if h!=EXPECTED: raise SystemExit(f"sha mismatch {h}")
out.write_bytes(data); print(f"PASS {out} {len(data)} {h}")
