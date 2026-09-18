import base64,pathlib,hashlib
root=pathlib.Path(__file__).resolve().parent
parts=[]
for i in range(9):
    parts.append((root/"source_chunks"/f"{i:02d}.b64").read_text())
raw=base64.b64decode("".join(parts))
want="7d264de601f475d0face9b4b4860cd58a4389133407f9fcb3fcde013ade94cdd"
got=hashlib.sha256(raw).hexdigest()
if got!=want: raise SystemExit(got)
(root/"experiment.py").write_bytes(raw)
print(got)
