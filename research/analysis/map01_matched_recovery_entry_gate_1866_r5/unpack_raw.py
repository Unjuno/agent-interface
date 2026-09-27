import base64,hashlib,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent
EXPECTED="7da951e4f745963049c313524341bf12aaa477265d86b9bc346af91c3e788e1d"
raw=base64.b64decode((HERE/"RAW.json.b64").read_text().strip(),validate=True)
assert hashlib.sha256(raw).hexdigest()==EXPECTED
out=pathlib.Path(sys.argv[1])
out.write_bytes(raw)
print(EXPECTED)
