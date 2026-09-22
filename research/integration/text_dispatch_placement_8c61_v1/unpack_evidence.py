from __future__ import annotations
import base64, hashlib, io, json, sys, tarfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent

def die(message: str) -> None:
    raise SystemExit(message)

if len(sys.argv) != 2:
    die("usage: unpack_evidence.py NEW_DEST")

dest = Path(sys.argv[1])
if dest.exists():
    die("destination already exists")

manifest = json.loads((ROOT / "PUBLICATION_MANIFEST.json").read_text())
capsule = manifest["formal_capsule"]
binary_parts = []
for row in capsule["binary_parts"]:
    encoded = "".join(
        "".join((ROOT / name).read_text().split())
        for name in row["text_files"]
    )
    try:
        raw = base64.b64decode(encoded, validate=True)
    except Exception as error:
        die(f"base64 failure part {row['index']}: {error}")
    if len(raw) != row["bytes"]:
        die(f"byte count mismatch part {row['index']}")
    if hashlib.sha256(raw).hexdigest() != row["sha256"]:
        die(f"sha256 mismatch part {row['index']}")
    binary_parts.append(raw)

archive = b"".join(binary_parts)
if len(archive) != capsule["bytes"]:
    die("capsule byte count mismatch")
if hashlib.sha256(archive).hexdigest() != capsule["sha256"]:
    die("capsule sha256 mismatch")

with tarfile.open(fileobj=io.BytesIO(archive), mode="r:xz") as tf:
    members = tf.getmembers()
    if len(members) != capsule["members_total"]:
        die("capsule member count mismatch")
    if sum(member.isfile() for member in members) != capsule["file_members"]:
        die("capsule file count mismatch")
    seen = set()
    for member in members:
        path = PurePosixPath(member.name)
        if path.is_absolute() or ".." in path.parts:
            die("unsafe archive path")
        if member.name in seen:
            die("duplicate archive path")
        if not (member.isfile() or member.isdir()):
            die("unsupported archive member")
        seen.add(member.name)
    dest.mkdir()
    tf.extractall(dest, filter="data")

print(json.dumps({
    "status": "PASS_FORMAL_CAPSULE_RETENTION_ONLY",
    "sha256": capsule["sha256"],
    "members_total": len(members),
    "file_members": sum(member.isfile() for member in members),
    "destination": str(dest),
}, sort_keys=True))
