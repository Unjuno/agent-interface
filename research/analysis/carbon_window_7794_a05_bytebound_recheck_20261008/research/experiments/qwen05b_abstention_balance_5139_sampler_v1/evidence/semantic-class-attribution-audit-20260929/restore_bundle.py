from __future__ import annotations
import base64
import hashlib
import io
from pathlib import Path, PurePosixPath
import zipfile

ROOT = Path(__file__).resolve().parent
EXPECTED_SIZE = 219085
EXPECTED_SHA256 = "3a853f78c501e6c2ac1f05dcdfe0c486ca979b49a126bda1328dfd4f0dc16445"

parts = sorted(ROOT.glob("CONTROL_BUNDLE.zip.part*.b64"))
if len(parts) != 19:
    raise SystemExit(f"part_count:{len(parts)}")
encoded = "".join(p.read_text(encoding="ascii").strip() for p in parts)
payload = base64.b64decode(encoded, validate=True)
if len(payload) != EXPECTED_SIZE:
    raise SystemExit(f"archive_size:{len(payload)}")
digest = hashlib.sha256(payload).hexdigest()
if digest != EXPECTED_SHA256:
    raise SystemExit(f"archive_sha256:{digest}")
with zipfile.ZipFile(io.BytesIO(payload)) as archive:
    bad = archive.testzip()
    if bad is not None:
        raise SystemExit(f"zip_crc:{bad}")
    for member in archive.infolist():
        name = PurePosixPath(member.filename)
        if name.is_absolute() or ".." in name.parts:
            raise SystemExit(f"unsafe_zip_path:{member.filename}")
    target = ROOT / "restored"
    archive.extractall(target)
print(f"PASS_RESTORE bytes={len(payload)} sha256={digest} files={len(archive.infolist())}")
