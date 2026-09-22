"""Read-only unpacker for the retained public API effect-separation evidence."""
from pathlib import Path
import argparse, base64, hashlib, json, tarfile, io

def main():
    p=argparse.ArgumentParser(); p.add_argument("destination", type=Path); a=p.parse_args()
    root=Path(__file__).resolve().parent
    if a.destination.exists(): raise SystemExit("destination exists")
    pack=json.loads((root/"PACK.json").read_text())
    decoded=[]
    for part in pack["parts"]:
        txt=(root/part["name"]).read_bytes()
        if hashlib.sha256(txt).hexdigest()!=part["text_sha256"]: raise SystemExit("part text hash mismatch")
        raw=base64.b64decode(txt, validate=True)
        if len(raw)!=part["decoded_bytes"] or hashlib.sha256(raw).hexdigest()!=part["decoded_sha256"]: raise SystemExit("part decoded mismatch")
        decoded.append(raw)
    archive=b"".join(decoded)
    if len(archive)!=pack["archive_bytes"] or hashlib.sha256(archive).hexdigest()!=pack["archive_sha256"]: raise SystemExit("archive mismatch")
    a.destination.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:xz") as tf:
        for m in tf.getmembers():
            target=(a.destination/m.name).resolve()
            if not target.is_relative_to(a.destination.resolve()): raise SystemExit("unsafe path")
        tf.extractall(a.destination, filter="data")
    print(json.dumps({"decision":"PASS_UNPACK","archive_sha256":pack["archive_sha256"],"parts":len(pack["parts"])},sort_keys=True))

if __name__=="__main__": main()
