import base64,hashlib,pathlib,sys
EXPECTED="8998116524231673c2c7fdc1c333e078bb9a8980aeb0257dae03efe20a228dba"
ROOT=pathlib.Path(__file__).parent
PARTS=[ROOT/f"evidence.part{i:02d}.b64" for i in range(5)]
out=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "grantor_cap_revocation_v1_evidence.tar.xz")
text="".join("".join(p.read_text().split()) for p in PARTS)
data=base64.b64decode(text); h=hashlib.sha256(data).hexdigest()
if h!=EXPECTED: raise SystemExit(f"sha mismatch {h}")
out.write_bytes(data); print(f"PASS {out} {len(data)} {h}")
