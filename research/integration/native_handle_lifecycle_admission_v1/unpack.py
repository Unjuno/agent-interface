import base64,hashlib,pathlib,tarfile,sys,io
here=pathlib.Path(__file__).resolve().parent
out=pathlib.Path(sys.argv[1]).resolve()
if out.exists(): raise SystemExit("destination exists")
parts=sorted(here.glob("bundle.part*.b64"))
blob=base64.b64decode("".join(p.read_text().strip() for p in parts),validate=True)
want="541a2fa19ef43d58782be966f1f6e07784ad76425cb4e306bafa58b46f3dcd97"
if hashlib.sha256(blob).hexdigest()!=want: raise SystemExit("bundle hash mismatch")
out.mkdir(parents=True)
with tarfile.open(fileobj=io.BytesIO(blob),mode="r:xz") as t:
    for m in t.getmembers():
        target=(out/m.name).resolve()
        if out not in target.parents and target!=out: raise SystemExit("unsafe path")
    t.extractall(out)
print("PASS_BUNDLE",len(parts),want)
