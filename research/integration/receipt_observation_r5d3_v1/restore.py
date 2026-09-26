"""Bounded, data-only restore; never execute archived code."""
import hashlib, io, json, lzma, pathlib, sys, tarfile
base = pathlib.Path(__file__).resolve().parent
kind, destination = sys.argv[1:]
if kind not in ("SOURCE", "EVIDENCE"):
    raise SystemExit("unknown capsule")
out = pathlib.Path(destination)
if out.exists():
    raise SystemExit("destination exists")
p = json.loads((base / (kind + "_PACK.json")).read_text())
parts = []
for part in p["parts"]:
    b = (base / part["name"]).read_bytes()
    if len(b) != part["bytes"] or hashlib.sha256(b).hexdigest() != part["sha256"]:
        raise SystemExit("part integrity")
    parts.append(b)
b = b"".join(parts)
if len(b) != p["bytes"] or hashlib.sha256(b).hexdigest() != p["sha256"]:
    raise SystemExit("capsule integrity")
d = lzma.LZMADecompressor(memlimit=128*1024*1024)
raw = d.decompress(b, max_length=32*1024*1024)
if not d.eof or d.unused_data:
    raise SystemExit("invalid or oversized expansion")
files = {}
with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as t:
    for m in t:
        q = pathlib.PurePosixPath(m.name)
        if not m.isfile() or q.is_absolute() or ".." in q.parts or str(q) != m.name or m.name in files:
            raise SystemExit("invalid member")
        f = t.extractfile(m)
        value = f.read()
        if hashlib.sha256(value).hexdigest() != p["members"].get(m.name):
            raise SystemExit("member integrity")
        files[m.name] = value
if set(files) != set(p["members"]) or sum(map(len, files.values())) != p["member_bytes"]:
    raise SystemExit("member denominator")
out.mkdir()
for rel, value in files.items():
    q = out / rel
    q.parent.mkdir(parents=True, exist_ok=True)
    q.write_bytes(value)
print(json.dumps({"files":len(files),"bytes":p["member_bytes"],"sha256":p["sha256"]},sort_keys=True))
