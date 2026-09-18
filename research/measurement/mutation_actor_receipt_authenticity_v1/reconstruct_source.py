import base64,pathlib,hashlib
root=pathlib.Path(__file__).resolve().parent
raw=base64.b64decode((root/"source_bundle.b64").read_text().strip())
want="c77ba9488b21968ef9d0c8e35ce4efacb0b698c534b61a7259ff02204edabf67"
got=hashlib.sha256(raw).hexdigest()
if got!=want: raise SystemExit(f"source hash mismatch {got}")
(root/"experiment.py").write_bytes(raw)
print(got)
