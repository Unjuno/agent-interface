import base64, hashlib, tarfile
from pathlib import Path

FILES={
 "SOURCE_BUNDLE.tar.gz.b64":"92be59148b9c8317fd78cf4cc6d766fa7e937f937799e3978d21f20cf63e2d14",
 "EVIDENCE_BUNDLE.tar.gz.b64":"1d7c39110d642d6d82f10e2e65c4b7dcb9efcacd8230ad2f8e5b3c3e3bef4d2b",
}
root=Path(__file__).resolve().parent
for name,expected in FILES.items():
    data=(root/name).read_bytes()
    actual=hashlib.sha256(data).hexdigest()
    if actual!=expected:
        raise SystemExit(f"{name}: hash mismatch {actual} != {expected}")
    raw=base64.b64decode(data)
    tgz=root/name.removesuffix(".b64")
    tgz.write_bytes(raw)
    with tarfile.open(tgz,"r:gz") as tf:
        tf.extractall(root/name.split(".")[0])
print("PASS_RECONSTRUCT")
