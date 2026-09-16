import base64,hashlib,pathlib
root=pathlib.Path(__file__).resolve().parent
src=root/"evidence.tar.xz.b64"
out=root/"mandatory_read_capability_v1_evidence.tar.xz"
data=base64.b64decode("".join(src.read_text().split()))
expected="9dcddbfe7570cf3086c3c5c5574b538e5763106ae9d04c4a508716663e2dca96"
assert hashlib.sha256(data).hexdigest()==expected
out.write_bytes(data)
print(out, len(data), expected)
