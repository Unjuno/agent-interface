import base64, hashlib, pathlib, sys
EXPECTED = "37bd3e2a61900ddb4907cf9cb251a9406e337626abcd644ed1bdb31b2b6e1e68"
src=pathlib.Path(__file__).with_name("evidence.tar.xz.b64")
out=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "exec_bound_socketcap_v1_evidence.tar.xz")
data=base64.b64decode("".join(src.read_text().split()))
h=hashlib.sha256(data).hexdigest()
if h!=EXPECTED: raise SystemExit(f"sha256 mismatch {h}")
out.write_bytes(data); print(f"PASS {out} {len(data)} {h}")
