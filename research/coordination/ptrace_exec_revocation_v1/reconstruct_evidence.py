import base64,hashlib,pathlib,sys
EXPECTED="e8aa327d40c01ab40eabad2be4103acd7c11e7ac6648be569c1410f82391351e"
ROOT=pathlib.Path(__file__).parent
PARTS=[ROOT/f"evidence.part{i:02d}.b64" for i in range(5)]
out=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "ptrace_exec_revocation_v1_evidence.tar.xz")
text="".join("".join(p.read_text().split()) for p in PARTS)
data=base64.b64decode(text)
h=hashlib.sha256(data).hexdigest()
if h!=EXPECTED: raise SystemExit(f"sha mismatch {h}")
out.write_bytes(data)
print(f"PASS {out} {len(data)} {h}")
