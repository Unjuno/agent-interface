import base64, hashlib, json, pathlib, sys, tarfile

def sha(b): return hashlib.sha256(b).hexdigest()
def main():
    here=pathlib.Path(__file__).resolve().parent
    out=pathlib.Path(sys.argv[1])
    if out.exists(): raise SystemExit("destination exists")
    m=json.loads((here/"SOURCE_CAPSULE.json").read_text())
    chunks=[]
    for p in m["parts"]:
        raw=(here/p["name"]).read_bytes()
        if sha(raw)!=p["sha256"]: raise SystemExit("part hash mismatch "+p["name"])
        text=raw.decode("ascii").strip()
        if len(text)!=p["chars"]: raise SystemExit("part length mismatch "+p["name"])
        chunks.append(text)
    archive=base64.b64decode("".join(chunks), validate=True)
    if len(archive)!=m["archive_bytes"] or sha(archive)!=m["archive_sha256"]:
        raise SystemExit("archive mismatch")
    out.mkdir()
    ap=out/"source.tar.xz"; ap.write_bytes(archive)
    with tarfile.open(ap,"r:xz") as tf:
        base=out.resolve()
        for member in tf.getmembers():
            target=(out/member.name).resolve()
            if target!=base and base not in target.parents:
                raise SystemExit("unsafe member")
        tf.extractall(out)
    print(m["archive_sha256"])
if __name__=="__main__": main()
