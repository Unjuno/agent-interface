"""Read-only verifier/extractor for Issue #4197 compact evidence.

This script never executes the study. It refuses an existing destination,
verifies every decoded archive before extraction, verifies the decompressed
formal RAW.json, and rejects unsafe tar paths.
"""
import base64
import gzip
import hashlib
import io
from pathlib import Path
import sys
import tarfile

HERE = Path(__file__).resolve().parent
DEST = Path(sys.argv[1]).resolve()
if DEST.exists():
    raise SystemExit("destination exists")

SPEC = {
    "sources.tar.gz.b64": ("99df9cc6382d17d9fbf4a88ade453037c719fa413375f65fcade216189dc819e", "tar", "sources"),
    "formal.raw.json.gz.b64": ("bf9807e4f2dd25d1de629ef872298e231ed57b3845569975f39920daf808e111", "raw", "formal"),
    "construction.tar.gz.b64": ("90a3669e484892fe4b28cae0aaf80fd4b9e6801b43955295bf9faeb2d9d52a7d", "tar", "construction"),
}
RAW_SHA = "b67790414851ebbe0ed82cb835eefc03b884ac89190d6d39040f004b416dd193"

def safe_extract_tar_gz(blob, out):
    out.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tf:
        members = tf.getmembers()
        for member in members:
            target = (out / member.name).resolve()
            if target != out and out not in target.parents:
                raise SystemExit("unsafe tar path")
            if member.issym() or member.islnk():
                raise SystemExit("links forbidden")
        tf.extractall(out)
    return len(members)

DEST.mkdir(parents=True)
receipt = {}
for filename, (want, kind, folder) in SPEC.items():
    encoded = (HERE / filename).read_text().strip()
    blob = base64.b64decode(encoded, validate=True)
    got = hashlib.sha256(blob).hexdigest()
    if got != want:
        raise SystemExit(f"{filename}: hash mismatch {got}")
    if kind == "tar":
        count = safe_extract_tar_gz(blob, DEST / folder)
        receipt[filename] = {"sha256": got, "members": count}
    else:
        raw = gzip.decompress(blob)
        raw_sha = hashlib.sha256(raw).hexdigest()
        if raw_sha != RAW_SHA or len(raw) != 12593:
            raise SystemExit("formal RAW mismatch")
        target = DEST / folder
        target.mkdir(parents=True)
        (target / "RAW.json").write_bytes(raw)
        receipt[filename] = {"sha256": got, "raw_sha256": raw_sha, "raw_bytes": len(raw)}
print("PASS_COMPACT_EVIDENCE", receipt)
