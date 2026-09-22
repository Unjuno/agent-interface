#!/usr/bin/env python3
import base64, hashlib, json, pathlib, sys, zipfile

root = pathlib.Path(__file__).resolve().parent
manifest = json.loads((root / "publication_parts" / "PACK.json").read_text())
out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/sqlite-readset-publication")
if out.exists():
    raise SystemExit("destination exists")
parts = []
for spec in manifest["parts"]:
    p = root / "publication_parts" / spec["name"]
    b = p.read_bytes()
    if len(b) != spec["chars"] or hashlib.sha256(b).hexdigest() != spec["sha256"]:
        raise SystemExit(f"part mismatch: {spec['name']}")
    parts.append(b)
raw = base64.b64decode(b"".join(parts), validate=True)
if len(raw) != manifest["zip_bytes"]:
    raise SystemExit("zip size mismatch")
if hashlib.sha256(raw).hexdigest() != manifest["zip_sha256"]:
    raise SystemExit("zip hash mismatch")
out.mkdir(parents=True)
zip_path = out / manifest["source_zip"]
zip_path.write_bytes(raw)
with zipfile.ZipFile(zip_path) as zf:
    for info in zf.infolist():
        target = (out / info.filename).resolve()
        if not str(target).startswith(str(out.resolve()) + "/"):
            raise SystemExit("unsafe member path")
    zf.extractall(out)
print(json.dumps({"pass": True, "zip_sha256": manifest["zip_sha256"], "destination": str(out)}, indent=2))
