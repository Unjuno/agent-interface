"""Restore the two exact data capsules into a new trusted private directory."""
import hashlib, io, json, lzma, pathlib, sys, tarfile
base = pathlib.Path(__file__).resolve().parent
out = pathlib.Path(sys.argv[1])
if out.exists():
    raise SystemExit("destination exists")
files = {}
for kind in ("SOURCE", "RAW"):
    p = json.loads((base / (kind + "_PACK.json")).read_text())
    chunks = []
    for item in p["parts"]:
        b = (base / item["name"]).read_bytes()
        if len(b) != item["bytes"] or hashlib.sha256(b).hexdigest() != item["sha256"]:
            raise SystemExit("part integrity")
        chunks.append(b)
    b = b"".join(chunks)
    if len(b) != p["bytes"] or hashlib.sha256(b).hexdigest() != p["sha256"]:
        raise SystemExit("archive integrity")
    dec = lzma.LZMADecompressor(memlimit=128*1024*1024)
    raw = dec.decompress(b, max_length=32*1024*1024)
    if not dec.eof or dec.unused_data:
        raise SystemExit("invalid or oversized archive")
    members = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as tf:
        for m in tf:
            q = pathlib.PurePosixPath(m.name)
            if not m.isfile() or q.is_absolute() or ".." in q.parts or str(q) != m.name or m.name in members or m.name in files:
                raise SystemExit("invalid member")
            members[m.name] = tf.extractfile(m).read()
    count = len(p["members"]) if kind == "SOURCE" else p["member_count"]
    if len(members) != count or sum(map(len, members.values())) != p["member_bytes"]:
        raise SystemExit("member denominator")
    if kind == "SOURCE" and {n:hashlib.sha256(b).hexdigest() for n,b in members.items()} != p["members"]:
        raise SystemExit("source member integrity")
    files.update(members)
out.mkdir()
for n, b in files.items():
    p = out / n
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b)
print(json.dumps({"files":len(files),"bytes":sum(map(len,files.values()))},sort_keys=True))
